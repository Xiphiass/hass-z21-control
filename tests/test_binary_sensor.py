"""Binary sensor platform tests for the Z21 Central State flags (issue #7).

The operational-status flags from the System State push exposed as binary
sensors, verified through the config-entry boundary with a faked UDP transport
(no physical Z21, no real socket). Mirrors ``test_sensor.py``: a ``Z21Client``
subclass whose ``open`` attaches a fake transport, and a scripted responder that
answers the handshake and feeds a ``LAN_SYSTEMSTATE_DATACHANGED`` datagram on a
System State poll.
"""

from __future__ import annotations

import struct

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, EntityCategory
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.z21 import protocol
from custom_components.z21.client import Z21Client
from custom_components.z21.const import (
    CONF_FW_VERSION,
    CONF_HW_TYPE,
    CONF_SERIAL,
    DOMAIN,
)

_HOST = "192.0.2.10"
_SERIAL = 0xABCD
_HW_TYPE = 0x00000201
_FW_VERSION = 0x0143

# CentralState bits (spec 2.18), CentralState byte at payload offset 12.
_EMERGENCY_STOP = 0x01
_SHORT_CIRCUIT = 0x04
_PROGRAMMING_MODE = 0x20
# CentralStateEx bits, byte at payload offset 13.
_HIGH_TEMPERATURE = 0x01
_POWER_LOST = 0x02

# key -> (central_state bit, central_state_ex bit, expected device_class or None)
_FAULTS = {
    "emergency_stop": (_EMERGENCY_STOP, 0, "problem"),
    "short_circuit": (_SHORT_CIRCUIT, 0, "problem"),
    "over_temperature": (0, _HIGH_TEMPERATURE, "problem"),
    "power_lost": (0, _POWER_LOST, "problem"),
    "programming_mode": (_PROGRAMMING_MODE, 0, None),
}


def _serial_response(serial: int) -> bytes:
    return protocol.build_frame(protocol.HDR_SERIAL_NUMBER, struct.pack("<I", serial))


def _hwinfo_response(hw: int, fw: int) -> bytes:
    return protocol.build_frame(protocol.HDR_HWINFO, struct.pack("<II", hw, fw))


def _system_state(central_state: int = 0, central_state_ex: int = 0) -> bytes:
    """Build a LAN_SYSTEMSTATE_DATACHANGED datagram with the given flag bytes."""
    electrical = struct.pack("<hhhhHH", 0, 0, 0, 20, 15000, 15000)
    tail = bytes([central_state, central_state_ex, 0, 0])
    return protocol.build_frame(
        protocol.HDR_SYSTEMSTATE_DATACHANGED, electrical + tail
    )


class _FakeTransport:
    """Records sends; invokes ``responder`` to script Z21 replies."""

    def __init__(self, client: Z21Client, responder) -> None:
        self.sent: list[bytes] = []
        self.closed = False
        self._client = client
        self._responder = responder

    def sendto(self, data: bytes, addr: object = None) -> None:
        self.sent.append(data)
        if self._responder is not None:
            header = int.from_bytes(data[2:4], "little")
            self._responder(header, self._client)

    def close(self) -> None:
        self.closed = True


def _responder(*, central_state: int = 0, central_state_ex: int = 0):
    """Answer the handshake and every System State poll with the given flags."""

    def responder(header, client):
        if header == protocol.HDR_SERIAL_NUMBER:
            client._on_datagram(_serial_response(_SERIAL))
        elif header == protocol.HDR_HWINFO:
            client._on_datagram(_hwinfo_response(_HW_TYPE, _FW_VERSION))
        elif header == protocol.HDR_SYSTEMSTATE_GETDATA:
            client._on_datagram(_system_state(central_state, central_state_ex))

    return responder


def _install_client(monkeypatch, *, responder) -> list[_FakeTransport]:
    transports: list[_FakeTransport] = []

    class _FakeClient(Z21Client):
        async def open(self) -> None:
            if self._transport is not None:
                return
            transport = _FakeTransport(self, responder)
            transports.append(transport)
            self._attach_transport(transport)

    monkeypatch.setattr("custom_components.z21.Z21Client", _FakeClient)
    monkeypatch.setattr("custom_components.z21.coordinator._STATE_TIMEOUT", 0.2)
    return transports


def _mock_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=str(_SERIAL),
        title=f"Z21 ({_HOST})",
        data={
            CONF_HOST: _HOST,
            CONF_SERIAL: _SERIAL,
            CONF_HW_TYPE: _HW_TYPE,
            CONF_FW_VERSION: _FW_VERSION,
        },
    )


def _entity_id(hass: HomeAssistant, key: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        "binary_sensor", DOMAIN, f"{_SERIAL}_{key}"
    )


async def test_all_faults_set(hass: HomeAssistant, monkeypatch) -> None:
    """Every fault flag set -> each sensor on with the right device_class."""
    all_central = _EMERGENCY_STOP | _SHORT_CIRCUIT | _PROGRAMMING_MODE
    all_ex = _HIGH_TEMPERATURE | _POWER_LOST
    _install_client(
        monkeypatch,
        responder=_responder(central_state=all_central, central_state_ex=all_ex),
    )
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for key, (_central, _ex, device_class) in _FAULTS.items():
        entity_id = _entity_id(hass, key)
        assert entity_id is not None, f"binary_sensor {key} not registered"
        state = hass.states.get(entity_id)
        assert state is not None, f"binary_sensor {key} has no state"
        assert state.state == "on"
        assert state.attributes.get("device_class") == device_class

    # Programming mode is a diagnostic entity.
    prog = er.async_get(hass).async_get(_entity_id(hass, "programming_mode"))
    assert prog is not None
    assert prog.entity_category == EntityCategory.DIAGNOSTIC


async def test_no_flags_all_off(hass: HomeAssistant, monkeypatch) -> None:
    """No flags set -> each fault sensor off."""
    _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for key in _FAULTS:
        state = hass.states.get(_entity_id(hass, key))
        assert state is not None, f"binary_sensor {key} has no state"
        assert state.state == "off"


async def test_push_toggles_each_flag(hass: HomeAssistant, monkeypatch) -> None:
    """An unsolicited System State push toggles each flag independently."""
    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    client = transports[0]._client
    for key, (central, ex, _device_class) in _FAULTS.items():
        entity_id = _entity_id(hass, key)
        assert hass.states.get(entity_id).state == "off"

        client._on_datagram(_system_state(central, ex))
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == "on", f"{key} did not turn on"

        # Clear all flags again for isolation between flags.
        client._on_datagram(_system_state())
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == "off"


async def test_excluded_bits_not_exposed(hass: HomeAssistant, monkeypatch) -> None:
    """Short-circuit-location bits and RCN213 produce no entities (per spec)."""
    _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for key in ("short_circuit_external", "short_circuit_internal", "rcn213"):
        assert _entity_id(hass, key) is None, f"{key} should not be exposed"
