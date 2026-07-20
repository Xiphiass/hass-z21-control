"""Integration setup tests for the Z21 coordinator + binary sensor (issue #5).

The end-to-end vertical slice, verified through the HA config-entry boundary with
a faked UDP transport (no physical Z21, no real socket). Mirrors the faking style
of ``test_config_flow.py``: a ``Z21Client`` subclass whose ``open`` attaches a
fake transport, and a scripted responder that answers the handshake and, on a
System State poll, feeds back a ``LAN_SYSTEMSTATE_DATACHANGED`` datagram.
"""

from __future__ import annotations

import asyncio
import struct

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
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

# CentralState.TRACK_VOLTAGE_OFF bit (protocol spec 2.18).
_TRACK_VOLTAGE_OFF = 0x02


def _serial_response(serial: int) -> bytes:
    return protocol.build_frame(protocol.HDR_SERIAL_NUMBER, struct.pack("<I", serial))


def _hwinfo_response(hw: int, fw: int) -> bytes:
    return protocol.build_frame(protocol.HDR_HWINFO, struct.pack("<II", hw, fw))


def _system_state(central_state: int = 0) -> bytes:
    """Build a LAN_SYSTEMSTATE_DATACHANGED datagram with the given flags."""
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


class _Responder:
    """Answers the handshake; answers System State polls while ``answer_state``.

    Mutable so a single loaded entry can be driven through silence (flip
    ``answer_state`` off) and recovery (flip it back on).
    """

    def __init__(self, *, answer_state: bool, central_state: int = 0) -> None:
        self.answer_state = answer_state
        self.central_state = central_state

    def __call__(self, header, client) -> None:
        if header == protocol.HDR_SERIAL_NUMBER:
            client._on_datagram(_serial_response(_SERIAL))
        elif header == protocol.HDR_HWINFO:
            client._on_datagram(_hwinfo_response(_HW_TYPE, _FW_VERSION))
        elif header == protocol.HDR_SYSTEMSTATE_GETDATA and self.answer_state:
            client._on_datagram(_system_state(self.central_state))


def _responder(*, answer_state: bool, central_state: int = 0) -> _Responder:
    """Answer the handshake; optionally answer System State polls."""
    return _Responder(answer_state=answer_state, central_state=central_state)


def _install_client(monkeypatch, *, responder) -> list[_FakeTransport]:
    """Patch ``__init__``'s ``Z21Client`` to fake the socket; shrink timeouts.

    Returns a list that the created transports are appended to, so a test can
    inspect what was sent / whether it was closed.
    """
    transports: list[_FakeTransport] = []

    class _FakeClient(Z21Client):
        async def open(self) -> None:
            if self._transport is not None:
                return
            transport = _FakeTransport(self, responder)
            transports.append(transport)
            self._attach_transport(transport)

    monkeypatch.setattr("custom_components.z21.Z21Client", _FakeClient)
    # The fake responder answers the handshake immediately, so connect returns
    # on its first attempt; only the System State wait needs shrinking. Shrink
    # the staleness window too so the liveness tests can sleep past it (issue #8).
    monkeypatch.setattr("custom_components.z21.coordinator._STATE_TIMEOUT", 0.2)
    monkeypatch.setattr("custom_components.z21.coordinator.STALENESS_WINDOW", 0.5)
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


def _track_voltage_entity_id(hass: HomeAssistant) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        "binary_sensor", DOMAIN, f"{_SERIAL}_track_voltage_off"
    )
    assert entity_id is not None
    return entity_id


async def test_setup_subscribes_and_keepalive(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Setup sends broadcast flag 0x00000100 and a System State poll."""
    transports = _install_client(
        monkeypatch, responder=_responder(answer_state=True)
    )
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    sent = transports[0].sent
    broadcast = protocol.build_frame(
        protocol.HDR_SET_BROADCASTFLAGS,
        struct.pack("<I", protocol.BROADCAST_FLAG_SYSTEM_STATE),
    )
    assert broadcast in sent
    assert protocol.build_frame(protocol.HDR_SYSTEMSTATE_GETDATA) in sent


async def test_push_updates_sensor(hass: HomeAssistant, monkeypatch) -> None:
    """A pushed System State toggles the track-voltage-off sensor."""
    transports = _install_client(
        monkeypatch, responder=_responder(answer_state=True, central_state=0)
    )
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_id = _track_voltage_entity_id(hass)
    state = hass.states.get(entity_id)
    assert state is not None
    # Track powered (bit clear) -> on, device_class power inverted.
    assert state.state == "on"
    assert state.attributes["device_class"] == "power"

    # Push an unsolicited DATACHANGED with track voltage off.
    client = transports[0]._client
    client._on_datagram(_system_state(_TRACK_VOLTAGE_OFF))
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "off"


async def test_setup_not_ready_without_system_state(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Handshake succeeds but no System State -> SETUP_RETRY (ConfigEntryNotReady)."""
    _install_client(monkeypatch, responder=_responder(answer_state=False))
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_closes_client(hass: HomeAssistant, monkeypatch) -> None:
    """Unloading tears down platforms and closes the live transport."""
    transports = _install_client(
        monkeypatch, responder=_responder(answer_state=True)
    )
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert transports[0].closed
    # A clean disconnect sends LAN_LOGOFF before tearing the socket down.
    assert protocol.build_frame(protocol.HDR_LOGOFF) in transports[0].sent


def _coordinator(hass: HomeAssistant):
    """The single loaded coordinator, for driving polls via async_refresh."""
    return next(iter(hass.data[DOMAIN].values()))


async def test_missed_poll_within_window_stays_available(
    hass: HomeAssistant, monkeypatch
) -> None:
    """A single silent poll within the staleness window keeps entities available."""
    responder = _responder(answer_state=True)
    transports = _install_client(monkeypatch, responder=responder)
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_id = _track_voltage_entity_id(hass)
    assert hass.states.get(entity_id).state == "on"

    # Go silent, then poll: the recent setup datagram is within the window.
    responder.answer_state = False
    await _coordinator(hass).async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state != "unavailable"


async def test_silence_past_window_marks_unavailable(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Silence past the staleness window greys out the entities."""
    responder = _responder(answer_state=True)
    transports = _install_client(monkeypatch, responder=responder)
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_id = _track_voltage_entity_id(hass)

    responder.answer_state = False
    # Sleep past the shrunk staleness window before polling.
    await asyncio.sleep(0.6)
    await _coordinator(hass).async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "unavailable"


async def test_recovery_resends_broadcast_flags(
    hass: HomeAssistant, monkeypatch
) -> None:
    """The first datagram after silence re-sends broadcast flags and recovers."""
    responder = _responder(answer_state=True)
    transports = _install_client(monkeypatch, responder=responder)
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_id = _track_voltage_entity_id(hass)
    broadcast = protocol.build_frame(
        protocol.HDR_SET_BROADCASTFLAGS,
        struct.pack("<I", protocol.BROADCAST_FLAG_SYSTEM_STATE),
    )
    # One broadcast-flags send at setup.
    assert transports[0].sent.count(broadcast) == 1

    # Fall past the window into unavailable.
    responder.answer_state = False
    await asyncio.sleep(0.6)
    await _coordinator(hass).async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "unavailable"

    # Z21 comes back: next poll reply recovers and re-sends the flags.
    responder.answer_state = True
    await _coordinator(hass).async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state != "unavailable"
    assert transports[0].sent.count(broadcast) == 2
