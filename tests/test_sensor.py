"""Sensor platform tests for the Z21 electrical telemetry (issue #6).

The six System State telemetry values exposed as HA sensors, verified through the
config-entry boundary with a faked UDP transport (no physical Z21, no real
socket). Mirrors ``test_init.py``: a ``Z21Client`` subclass whose ``open``
attaches a fake transport, and a scripted responder that answers the handshake
and feeds a ``LAN_SYSTEMSTATE_DATACHANGED`` datagram on a System State poll.
"""

from __future__ import annotations

import struct

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST
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

# Distinct, nonzero electrical values so each sensor is asserted independently.
# Wire order: main, prog, filtered_main, temperature, supply, vcc (spec 2.18).
_MAIN_CURRENT = 111
_PROG_CURRENT = 222
_FILTERED_MAIN_CURRENT = 333
_TEMPERATURE = 27
_SUPPLY_VOLTAGE = 18000
_TRACK_VOLTAGE = 15500

# name -> (unique_id suffix, expected native value, device_class, unit)
_EXPECTED = {
    "main_current": (_MAIN_CURRENT, "current", "mA"),
    "filtered_main_current": (_FILTERED_MAIN_CURRENT, "current", "mA"),
    "prog_current": (_PROG_CURRENT, "current", "mA"),
    "temperature": (_TEMPERATURE, "temperature", "°C"),
    "supply_voltage": (_SUPPLY_VOLTAGE, "voltage", "mV"),
    "track_voltage": (_TRACK_VOLTAGE, "voltage", "mV"),
}


def _serial_response(serial: int) -> bytes:
    return protocol.build_frame(protocol.HDR_SERIAL_NUMBER, struct.pack("<I", serial))


def _hwinfo_response(hw: int, fw: int) -> bytes:
    return protocol.build_frame(protocol.HDR_HWINFO, struct.pack("<II", hw, fw))


def _system_state(
    *,
    main: int = _MAIN_CURRENT,
    prog: int = _PROG_CURRENT,
    filtered_main: int = _FILTERED_MAIN_CURRENT,
    temperature: int = _TEMPERATURE,
    supply: int = _SUPPLY_VOLTAGE,
    vcc: int = _TRACK_VOLTAGE,
) -> bytes:
    """Build a LAN_SYSTEMSTATE_DATACHANGED datagram with electrical values."""
    electrical = struct.pack(
        "<hhhhHH", main, prog, filtered_main, temperature, supply, vcc
    )
    tail = bytes([0, 0, 0, 0])
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


def _responder(header, client):
    """Answer the handshake and every System State poll."""
    if header == protocol.HDR_SERIAL_NUMBER:
        client._on_datagram(_serial_response(_SERIAL))
    elif header == protocol.HDR_HWINFO:
        client._on_datagram(_hwinfo_response(_HW_TYPE, _FW_VERSION))
    elif header == protocol.HDR_SYSTEMSTATE_GETDATA:
        client._on_datagram(_system_state())


def _install_client(monkeypatch) -> list[_FakeTransport]:
    transports: list[_FakeTransport] = []

    class _FakeClient(Z21Client):
        async def open(self) -> None:
            if self._transport is not None:
                return
            transport = _FakeTransport(self, _responder)
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


def _entity_id(hass: HomeAssistant, key: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{_SERIAL}_{key}"
    )
    assert entity_id is not None, f"sensor {key} not registered"
    return entity_id


async def test_all_sensors_reflect_pushed_state(
    hass: HomeAssistant, monkeypatch
) -> None:
    """All six sensors appear with correct values, device classes, and units."""
    _install_client(monkeypatch)
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for key, (value, device_class, unit) in _EXPECTED.items():
        state = hass.states.get(_entity_id(hass, key))
        assert state is not None, f"sensor {key} has no state"
        assert state.state == str(value)
        assert state.attributes["device_class"] == device_class
        assert state.attributes["unit_of_measurement"] == unit
        assert state.attributes["state_class"] == "measurement"


async def test_push_updates_sensors(hass: HomeAssistant, monkeypatch) -> None:
    """An unsolicited System State push updates the sensor values."""
    _install_client(monkeypatch)
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    main_id = _entity_id(hass, "main_current")
    assert hass.states.get(main_id).state == str(_MAIN_CURRENT)

    # Push a new snapshot with a changed main-track current.
    client = hass.data[DOMAIN][entry.entry_id].client
    client._on_datagram(_system_state(main=999))
    await hass.async_block_till_done()

    assert hass.states.get(main_id).state == "999"
