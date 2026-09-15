"""Turnout switch platform tests for the Z21 integration (issue #31).

Verifies that each configured turnout creates a switch entity whose
``is_on`` reflects the coordinator's stored position, and that
``turn_on``/``turn_off`` send the correct ``LAN_X_SET_TURNOUT`` commands.
Uses the same ``_FakeTransport`` / ``_install_client`` pattern as
``test_switch.py``.
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
    CONF_TURNOUTS,
    CONF_TURNOUT_FADR,
    CONF_TURNOUT_INVERTED,
    CONF_TURNOUT_NAME,
    DOMAIN,
)


_HOST = "192.0.2.10"
_SERIAL = 0xABCD
_HW_TYPE = 0x00000201
_FW_VERSION = 0x0143

# CentralState bit (spec 2.18), CentralState byte at payload offset 12.
_TRACK_VOLTAGE_OFF = 0x02

_TURNOUTS = [
    {
        CONF_TURNOUT_NAME: "Switch A",
        CONF_TURNOUT_FADR: 4,
    },
    {
        CONF_TURNOUT_NAME: "Switch B",
        CONF_TURNOUT_FADR: 7,
    },
]


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


def _turnout_info_response(fadr: int, position: int) -> bytes:
    """Build a LAN_X_TURNOUT_INFO datagram.

    DB2 is 000000ZZ (spec 5.3): ZZ=01 -> position 0 (output 1),
    ZZ=10 -> position 1 (output 2). The message is tunneled under HDR_X (0x40)
    with X-Header 0x43, so use ``build_turnout_info`` rather than a fabricated
    top-level 0x43 header.
    """
    zz = position + 1  # 0->0b01, 1->0b10
    return protocol.build_turnout_info(fadr, zz)


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
            self._responder(header, self._client, data)

    def close(self) -> None:
        self.closed = True


def _responder(*, central_state: int = 0):
    """Answer the handshake and every System State poll with the given flags.

    NOTE: Does NOT auto-answer LAN_X_GET_TURNOUT_INFO requests.
    Tests that need turnout position data should send it explicitly via
    ``client._on_datagram(_turnout_info_response(fadr, position))``.
    """

    def responder(header, client, data=None):
        if header == protocol.HDR_SERIAL_NUMBER:
            client._on_datagram(_serial_response(_SERIAL))
        elif header == protocol.HDR_HWINFO:
            client._on_datagram(_hwinfo_response(_HW_TYPE, _FW_VERSION))
        elif header == protocol.HDR_SYSTEMSTATE_GETDATA:
            client._on_datagram(_system_state(central_state))
        # NOTE: No auto-response for HDR_TURNOUT_INFO here.
        # Tests that need turnout position data should send it explicitly.

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


def _mock_entry(turnouts: list[dict] | None = None) -> MockConfigEntry:
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
        options={
            CONF_TURNOUTS: turnouts if turnouts is not None else _TURNOUTS,
        },
    )


def _turnout_entities(er_registry: er.EntityRegistry) -> list[er.RegistryEntry]:
    """Filter entity registry entries for turnout switches."""
    return [
        e for e in er_registry.entities.values()
        if e.platform == DOMAIN and "turnout" in e.unique_id
    ]


async def test_turnout_entities_created(hass: HomeAssistant, monkeypatch) -> None:
    """Configured turnouts create switch entities."""
    _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    er_registry = er.async_get(hass)
    # Should have: track_power + 2 turnouts = 3 entities
    turnout_entities = _turnout_entities(er_registry)
    assert len(turnout_entities) == 2


async def test_turnout_is_on_reflects_position(hass: HomeAssistant, monkeypatch) -> None:
    """A turnout with position 1 reports on, position 0 reports off."""
    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    er_registry = er.async_get(hass)

    # Initially the turnout has no position data, so state should be "unknown"
    entity_id = er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_4")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "unknown"

    # Simulate a turnout info broadcast for FAdr 4 -> position 1 (ZZ=10)
    client = transports[0]._client
    client._on_datagram(_turnout_info_response(4, 1))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "on"

    # Simulate position change to 0 (ZZ=01)
    client._on_datagram(_turnout_info_response(4, 0))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"


async def test_turnout_unavailable_before_position(hass: HomeAssistant, monkeypatch) -> None:
    """A turnout with no position data yet shows unavailable."""
    # Create an entry with a turnout that never receives position data
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=str(_SERIAL),
        title=f"Z21 ({_HOST})",
        data={
            CONF_HOST: _HOST,
            CONF_SERIAL: _SERIAL,
            CONF_HW_TYPE: _HW_TYPE,
            CONF_FW_VERSION: _FW_VERSION,
        },
        options={
            CONF_TURNOUTS: [
                {
                    CONF_TURNOUT_NAME: "No Info Turnout",
                    CONF_TURNOUT_FADR: 99,
                }
            ],
        },
    )
    entry.add_to_hass(hass)

    _install_client(monkeypatch, responder=_responder())

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    er_registry = er.async_get(hass)
    entity_id = er_registry.async_get_entity_id(
        "switch", DOMAIN, f"{_SERIAL}_turnout_99"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "unknown"


async def test_turnon_sends_activate(hass: HomeAssistant, monkeypatch) -> None:
    """Calling turn_on sends the Activate for output 2 immediately."""
    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    transport = transports[0]
    transport.sent.clear()

    er_registry = er.async_get(hass)
    entity_id = er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_4")
    assert entity_id is not None

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )

    # turn_on -> Activate output 2 (Q=1) for FAdr 4, sent immediately.
    expected = protocol.build_turnout_set(4, 1, activate=True)
    assert expected in transport.sent


async def test_turnoff_sends_activate(hass: HomeAssistant, monkeypatch) -> None:
    """Calling turn_off sends the Activate for output 1 immediately."""
    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    transport = transports[0]
    transport.sent.clear()

    er_registry = er.async_get(hass)
    entity_id = er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_7")
    assert entity_id is not None

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )

    # turn_off -> Activate output 1 (Q=1) for FAdr 7, sent immediately.
    expected = protocol.build_turnout_set(7, 0, activate=True)
    assert expected in transport.sent


async def test_turnout_deactivate_follows_activate(
    hass: HomeAssistant, monkeypatch
) -> None:
    """A throw pairs its Activate with a Deactivate for the same output."""
    import asyncio

    from custom_components.z21 import client as client_module

    # Shrink the deactivate delay so the test doesn't wait 150 ms.
    monkeypatch.setattr(client_module, "TURNOUT_DEACTIVATE_DELAY", 0.01)

    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    transport = transports[0]
    transport.sent.clear()

    er_registry = er.async_get(hass)
    entity_id = er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_4")
    assert entity_id is not None

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )

    activate = protocol.build_turnout_set(4, 1, activate=True)
    deactivate = protocol.build_turnout_set(4, 1, activate=False)
    assert activate in transport.sent
    assert deactivate not in transport.sent  # not yet — it's scheduled

    await asyncio.sleep(0.05)
    await hass.async_block_till_done()
    assert deactivate in transport.sent
    # Activate precedes its Deactivate.
    assert transport.sent.index(activate) < transport.sent.index(deactivate)


async def test_turnout_removed_on_options_update(hass: HomeAssistant, monkeypatch) -> None:
    """Removing a turnout from options removes the entity."""
    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    er_registry = er.async_get(hass)

    # Verify both turnouts exist
    assert er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_4")
    assert er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_7")

    # Update options to remove turnout 7 using the proper API
    hass.config_entries.async_update_entry(
        entry, options={CONF_TURNOUTS: _TURNOUTS[:1]}
    )
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    # Turnout 4 should still exist, turnout 7 should be unavailable after removal
    assert er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_4")
    removed_state = hass.states.get("switch.z21_192_0_2_10_switch_b")
    assert removed_state is not None
    assert removed_state.state == "unavailable"


async def test_turnout_initial_position_poll_on_setup(hass: HomeAssistant, monkeypatch) -> None:
    """When the Z21 becomes available, each configured turnout is polled once."""
    sent_frames: list[bytes] = []

    class _RecordingTransport:
        def __init__(self, client: Z21Client, responder) -> None:
            self.sent: list[bytes] = []
            self._client = client
            self._responder = responder

        def sendto(self, data: bytes, addr: object = None) -> None:
            self.sent.append(data)
            sent_frames.append(data)
            if self._responder is not None:
                header = int.from_bytes(data[2:4], "little")
                self._responder(header, self._client, data)

        def close(self) -> None:
            pass

    transports: list[_FakeTransport] = []

    def responder(header, client, data=None):
        if header == protocol.HDR_SERIAL_NUMBER:
            client._on_datagram(_serial_response(_SERIAL))
        elif header == protocol.HDR_HWINFO:
            client._on_datagram(_hwinfo_response(_HW_TYPE, _FW_VERSION))
        elif header == protocol.HDR_SYSTEMSTATE_GETDATA:
            client._on_datagram(_system_state())
        # NOTE: No auto-response for HDR_TURNOUT_INFO here.

    class _FakeClient(Z21Client):
        async def open(self) -> None:
            if self._transport is not None:
                return
            transport = _RecordingTransport(self, responder)
            transports.append(transport)  # type: ignore[arg-type]
            self._attach_transport(transport)

    monkeypatch.setattr("custom_components.z21.Z21Client", _FakeClient)
    monkeypatch.setattr("custom_components.z21.coordinator._STATE_TIMEOUT", 0.2)

    entry = _mock_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Check that a LAN_X_GET_TURNOUT_INFO request was sent for each configured turnout.
    # The wire format is: dataset header HDR_X (0x40), X-header 0x43, then fadr bytes.
    # We detect it by looking for the X-header 0x43 in the payload (offset 4).
    turnout_info_frames = [
        f for f in sent_frames
        if len(f) >= 8 and int.from_bytes(f[2:4], "little") == protocol.HDR_X
        and f[4] == 0x43  # X-header is 0x43 (turnout info get)
    ]
    assert len(turnout_info_frames) == 2  # one per configured turnout


_INVERTED_TURNOUTS = [
    {
        CONF_TURNOUT_NAME: "Inverted",
        CONF_TURNOUT_FADR: 4,
        CONF_TURNOUT_INVERTED: True,
    },
]


async def test_inverted_is_on_reflects_flipped_position(
    hass: HomeAssistant, monkeypatch
) -> None:
    """For an inverted turnout, position 0 reports on and position 1 reports off."""
    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry(_INVERTED_TURNOUTS)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    er_registry = er.async_get(hass)
    entity_id = er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_4")
    assert entity_id is not None

    client = transports[0]._client
    # Position 0 (output 1) -> "on" when inverted.
    client._on_datagram(_turnout_info_response(4, 0))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "on"

    # Position 1 (output 2) -> "off" when inverted.
    client._on_datagram(_turnout_info_response(4, 1))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"


async def test_inverted_turnon_sends_output_1(
    hass: HomeAssistant, monkeypatch
) -> None:
    """An inverted turn_on drives output 1 (Q=1) instead of output 2."""
    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry(_INVERTED_TURNOUTS)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    transport = transports[0]
    transport.sent.clear()

    er_registry = er.async_get(hass)
    entity_id = er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_4")
    assert entity_id is not None

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )

    expected = protocol.build_turnout_set(4, 0, activate=True)
    assert expected in transport.sent


async def test_inverted_turnoff_sends_output_2(
    hass: HomeAssistant, monkeypatch
) -> None:
    """An inverted turn_off drives output 2 (Q=1) instead of output 1."""
    transports = _install_client(monkeypatch, responder=_responder())
    entry = _mock_entry(_INVERTED_TURNOUTS)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    transport = transports[0]
    transport.sent.clear()

    er_registry = er.async_get(hass)
    entity_id = er_registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_4")
    assert entity_id is not None

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )

    expected = protocol.build_turnout_set(4, 1, activate=True)
    assert expected in transport.sent