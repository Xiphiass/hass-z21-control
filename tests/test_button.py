"""Button platform tests for the Z21 emergency-stop control (issue #19).

The second control surface, verified through the config-entry boundary with a
faked UDP transport (no physical Z21, no real socket). Mirrors
``test_switch.py``: a ``Z21Client`` subclass whose ``open`` attaches a fake
transport, and a scripted responder that answers the handshake and feeds a
``LAN_SYSTEMSTATE_DATACHANGED`` datagram on a System State poll. The button is
stateless (ADR-0002): pressing it fires ``LAN_X_SET_STOP`` over the send seam,
and the existing ``emergency_stop`` binary sensor remains its feedback.
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

# CentralState bit (spec 2.18), CentralState byte at payload offset 12.
_EMERGENCY_STOP = 0x01


def _serial_response(serial: int) -> bytes:
    return protocol.build_frame(protocol.HDR_SERIAL_NUMBER, struct.pack("<I", serial))


def _hwinfo_response(hw: int, fw: int) -> bytes:
    return protocol.build_frame(protocol.HDR_HWINFO, struct.pack("<II", hw, fw))


def _system_state(central_state: int = 0) -> bytes:
    """Build a LAN_SYSTEMSTATE_DATACHANGED datagram with the given flag byte."""
    electrical = struct.pack("<hhhhHH", 0, 0, 0, 20, 15000, 15000)
    tail = bytes([central_state, 0, 0, 0])
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


def _responder(*, central_state: int = 0):
    """Answer the handshake and every System State poll with the given flags."""

    def responder(header, client):
        if header == protocol.HDR_SERIAL_NUMBER:
            client._on_datagram(_serial_response(_SERIAL))
        elif header == protocol.HDR_HWINFO:
            client._on_datagram(_hwinfo_response(_HW_TYPE, _FW_VERSION))
        elif header == protocol.HDR_SYSTEMSTATE_GETDATA:
            client._on_datagram(_system_state(central_state))

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


def _entity_id(hass: HomeAssistant) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        "button", DOMAIN, f"{_SERIAL}_emergency_stop"
    )


async def test_button_registered_and_stateless(
    hass: HomeAssistant, monkeypatch
) -> None:
    """The emergency-stop button is registered with no device_class."""
    _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_id = _entity_id(hass)
    assert entity_id is not None, "button emergency_stop not registered"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes.get("device_class") is None


async def test_press_sends_set_stop(hass: HomeAssistant, monkeypatch) -> None:
    """Pressing the button sends LAN_X_SET_STOP."""
    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    transport = transports[0]
    transport.sent.clear()
    await hass.services.async_call(
        "button", "press", {"entity_id": _entity_id(hass)}, blocking=True
    )
    assert protocol.build_set_stop() in transport.sent


async def test_emergency_stop_binary_sensor_reflects_state(
    hass: HomeAssistant, monkeypatch
) -> None:
    """The button is fire-and-forget; the binary sensor is the feedback."""
    transports = _install_client(
        monkeypatch, responder=_responder(central_state=_EMERGENCY_STOP)
    )
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    sensor_id = er.async_get(hass).async_get_entity_id(
        "binary_sensor", DOMAIN, f"{_SERIAL}_emergency_stop"
    )
    assert hass.states.get(sensor_id).state == "on"

    # Clearing the flag (e.g. after track power back on) flips the sensor.
    client = transports[0]._client
    client._on_datagram(_system_state())
    await hass.async_block_till_done()
    assert hass.states.get(sensor_id).state == "off"
