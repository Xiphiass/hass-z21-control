"""Loco drive entity tests for the Z21 integration (issue #49).

Each configured loco becomes its own HA Device (nested under the station via
``via_device_id``) carrying a speed ``number``, a direction ``switch`` and an
E-Stop ``button``. All three are non-optimistic: state follows the
coordinator's last-known ``LocoInfo``, and every action emits a
``LAN_X_SET_LOCO_DRIVE`` composed from it (ADR-0003). Uses the same
``_FakeTransport`` / ``_install_client`` pattern as ``test_turnout_switch.py``.
"""

from __future__ import annotations

import logging
import struct

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.z21 import protocol
from custom_components.z21.client import Z21Client
from custom_components.z21.const import (
    CONF_FW_VERSION,
    CONF_HW_TYPE,
    CONF_LOCO_ADDRESS,
    CONF_LOCO_ID,
    CONF_LOCO_NAME,
    CONF_LOCO_SPEED_STEPS,
    CONF_LOCOS,
    CONF_SERIAL,
    DOMAIN,
)


_HOST = "192.0.2.10"
_SERIAL = 0xABCD
_HW_TYPE = 0x00000201
_FW_VERSION = 0x0143

_LOCOS = [
    {
        CONF_LOCO_ID: "loco-br218",
        CONF_LOCO_NAME: "BR 218",
        CONF_LOCO_ADDRESS: 3,
        CONF_LOCO_SPEED_STEPS: 128,
    },
    {
        CONF_LOCO_ID: "loco-v100",
        CONF_LOCO_NAME: "V 100",
        CONF_LOCO_ADDRESS: 300,
        CONF_LOCO_SPEED_STEPS: 28,
    },
    {
        CONF_LOCO_ID: "loco-koef",
        CONF_LOCO_NAME: "Köf",
        CONF_LOCO_ADDRESS: 7,
        CONF_LOCO_SPEED_STEPS: 14,
    },
]


def _serial_response(serial: int) -> bytes:
    return protocol.build_frame(protocol.HDR_SERIAL_NUMBER, struct.pack("<I", serial))


def _hwinfo_response(hw: int, fw: int) -> bytes:
    return protocol.build_frame(protocol.HDR_HWINFO, struct.pack("<II", hw, fw))


def _system_state() -> bytes:
    electrical = struct.pack("<hhhhHH", 0, 0, 0, 20, 15000, 15000)
    return protocol.build_frame(
        protocol.HDR_SYSTEMSTATE_DATACHANGED, electrical + bytes(4)
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
        header = int.from_bytes(data[2:4], "little")
        self._responder(header, self._client)

    def close(self) -> None:
        self.closed = True


def _responder(header, client):
    """Answer the handshake and System State polls; loco info is sent by tests."""
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


def _mock_entry(locos: list[dict] | None = None) -> MockConfigEntry:
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
        options={CONF_LOCOS: locos if locos is not None else _LOCOS},
    )


async def _setup(hass: HomeAssistant, monkeypatch) -> _FakeTransport:
    transports = _install_client(monkeypatch)
    entry = _mock_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return transports[0]


def _entity_id(hass: HomeAssistant, platform: str, address: int, suffix: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{_SERIAL}_loco_{address}_{suffix}"
    )
    assert entity_id is not None
    return entity_id


async def _feed(hass: HomeAssistant, transport: _FakeTransport, **info) -> None:
    """Deliver a LAN_X_LOCO_INFO as if the Z21 pushed it."""
    transport._client._on_datagram(protocol.build_loco_info(**info))
    await hass.async_block_till_done()


def _drive(address: int, *, step: int, forward: bool, speed_steps: int,
           estop: bool = False) -> bytes:
    return protocol.build_loco_drive(
        address, step=step, forward=forward, speed_steps=speed_steps, estop=estop
    )


# --- Devices ----------------------------------------------------------------


async def test_each_loco_is_a_device_under_the_station(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Every loco is its own Device, nested under the Z21 via ``via_device_id``."""
    await _setup(hass, monkeypatch)

    dev_reg = dr.async_get(hass)
    entry_id = hass.config_entries.async_entries(DOMAIN)[0].entry_id
    station = dev_reg.async_get_device_by_identifier((DOMAIN, str(_SERIAL)), entry_id)
    assert station is not None

    ent_reg = er.async_get(hass)
    for loco in _LOCOS:
        address = loco[CONF_LOCO_ADDRESS]
        device_ids = {
            ent_reg.async_get(_entity_id(hass, platform, address, suffix)).device_id
            for platform, suffix in (
                ("number", "speed"),
                ("switch", "direction"),
                ("button", "estop"),
            )
        }
        # All three drive entities share one per-loco Device.
        assert len(device_ids) == 1
        device = dev_reg.async_get(device_ids.pop())
        assert device.name == loco[CONF_LOCO_NAME]
        assert device.via_device_id == station.id
        assert device.id != station.id


# --- Speed number -------------------------------------------------------------


async def test_speed_range_follows_step_mode(hass: HomeAssistant, monkeypatch) -> None:
    """The slider max is the loco's step count: 126 / 28 / 14, step 1."""
    await _setup(hass, monkeypatch)

    for address, maximum in ((3, 126), (300, 28), (7, 14)):
        state = hass.states.get(_entity_id(hass, "number", address, "speed"))
        assert state.attributes["min"] == 0
        assert state.attributes["max"] == maximum
        assert state.attributes["step"] == 1


async def test_speed_state_follows_loco_info(hass: HomeAssistant, monkeypatch) -> None:
    """Unknown until feedback, then tracks every reported step (incl. external)."""
    transport = await _setup(hass, monkeypatch)
    entity_id = _entity_id(hass, "number", 3, "speed")
    assert hass.states.get(entity_id).state == "unknown"

    await _feed(hass, transport, address=3, forward=True, step=42, speed_steps=128)
    assert float(hass.states.get(entity_id).state) == 42

    # A handset moves the loco: HA follows.
    await _feed(hass, transport, address=3, forward=False, step=7, speed_steps=128)
    assert float(hass.states.get(entity_id).state) == 7

    # An E-Stop reads as standstill.
    await _feed(hass, transport, address=3, forward=False, step=0, speed_steps=128,
                estop=True)
    assert float(hass.states.get(entity_id).state) == 0


async def test_speed_above_max_is_clamped_and_logged(
    hass: HomeAssistant, monkeypatch, caplog
) -> None:
    """A 28-step loco the Z21 reports in 128-step mode clamps to 28 and warns."""
    transport = await _setup(hass, monkeypatch)
    entity_id = _entity_id(hass, "number", 300, "speed")

    with caplog.at_level(logging.WARNING):
        await _feed(hass, transport, address=300, forward=True, step=100,
                    speed_steps=128)

    assert float(hass.states.get(entity_id).state) == 28
    assert any(
        "300" in r.getMessage() and "100" in r.getMessage() for r in caplog.records
    )


async def test_set_speed_composes_last_known_direction(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Setting speed sends a drive command keeping the reported direction."""
    transport = await _setup(hass, monkeypatch)
    await _feed(hass, transport, address=300, forward=False, step=5, speed_steps=28)
    entity_id = _entity_id(hass, "number", 300, "speed")
    transport.sent.clear()

    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 20}, blocking=True
    )

    assert transport.sent == [_drive(300, step=20, forward=False, speed_steps=28)]
    # Non-optimistic: the state waits for the Z21's echo.
    assert float(hass.states.get(entity_id).state) == 5


async def test_set_speed_before_feedback_defaults_forward(
    hass: HomeAssistant, monkeypatch
) -> None:
    """With no feedback yet, a speed command defaults to forward (ADR-0003)."""
    transport = await _setup(hass, monkeypatch)
    entity_id = _entity_id(hass, "number", 7, "speed")
    transport.sent.clear()

    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 9}, blocking=True
    )

    assert transport.sent == [_drive(7, step=9, forward=True, speed_steps=14)]


async def test_set_speed_zero_sends_normal_stop(hass: HomeAssistant, monkeypatch) -> None:
    """Speed 0 is a normal Stop (``R0000000``), not an E-Stop."""
    transport = await _setup(hass, monkeypatch)
    await _feed(hass, transport, address=3, forward=True, step=60, speed_steps=128)
    entity_id = _entity_id(hass, "number", 3, "speed")
    transport.sent.clear()

    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 0}, blocking=True
    )

    assert transport.sent == [_drive(3, step=0, forward=True, speed_steps=128)]
    assert transport.sent[0][-2] == 0x80  # DB3: forward, Stop


# --- Direction switch -----------------------------------------------------------


async def test_direction_state_follows_loco_info(
    hass: HomeAssistant, monkeypatch
) -> None:
    """On = forward; unknown until feedback, then follows external changes."""
    transport = await _setup(hass, monkeypatch)
    entity_id = _entity_id(hass, "switch", 3, "direction")
    assert hass.states.get(entity_id).state == "unknown"

    await _feed(hass, transport, address=3, forward=True, step=0, speed_steps=128)
    assert hass.states.get(entity_id).state == "on"

    await _feed(hass, transport, address=3, forward=False, step=0, speed_steps=128)
    assert hass.states.get(entity_id).state == "off"


async def test_direction_flip_keeps_current_speed(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Flipping direction sends the new direction at the current speed."""
    transport = await _setup(hass, monkeypatch)
    await _feed(hass, transport, address=3, forward=True, step=50, speed_steps=128)
    entity_id = _entity_id(hass, "switch", 3, "direction")
    transport.sent.clear()

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert transport.sent == [_drive(3, step=50, forward=False, speed_steps=128)]
    # Non-optimistic: still forward until the Z21 reports otherwise.
    assert hass.states.get(entity_id).state == "on"

    transport.sent.clear()
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert transport.sent == [_drive(3, step=50, forward=True, speed_steps=128)]


# --- E-Stop button ------------------------------------------------------------


async def test_estop_preserves_last_known_direction(
    hass: HomeAssistant, monkeypatch
) -> None:
    """The per-loco E-Stop sends ``R0000001`` keeping the reported direction."""
    transport = await _setup(hass, monkeypatch)
    await _feed(hass, transport, address=300, forward=False, step=12, speed_steps=28)
    entity_id = _entity_id(hass, "button", 300, "estop")
    transport.sent.clear()

    await hass.services.async_call(
        "button", "press", {"entity_id": entity_id}, blocking=True
    )

    assert transport.sent == [
        _drive(300, step=0, forward=False, speed_steps=28, estop=True)
    ]
    assert transport.sent[0][-2] == 0x01  # DB3: reverse, E-Stop


async def test_estop_is_not_the_station_wide_stop(
    hass: HomeAssistant, monkeypatch
) -> None:
    """The loco E-Stop never sends ``LAN_X_SET_STOP`` (station-wide halt)."""
    transport = await _setup(hass, monkeypatch)
    entity_id = _entity_id(hass, "button", 3, "estop")
    transport.sent.clear()

    await hass.services.async_call(
        "button", "press", {"entity_id": entity_id}, blocking=True
    )

    assert protocol.build_set_stop() not in transport.sent
    assert transport.sent == [
        _drive(3, step=0, forward=True, speed_steps=128, estop=True)
    ]


async def test_direction_flip_keeps_reported_step_mode(
    hass: HomeAssistant, monkeypatch
) -> None:
    """A direction flip is sent in the mode the Z21 reported, not the configured one.

    Rewriting a 128-reported loco into its configured 14-step mode would store
    that mode for the address (§4.2) and change its speed (ADR-0003).
    """
    transport = await _setup(hass, monkeypatch)
    # Köf is configured for 14 steps, but the Z21 reports it in 128-step mode.
    await _feed(hass, transport, address=7, forward=True, step=100, speed_steps=128)
    entity_id = _entity_id(hass, "switch", 7, "direction")
    transport.sent.clear()

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )

    assert transport.sent == [_drive(7, step=100, forward=False, speed_steps=128)]


async def test_set_speed_rescales_into_reported_mode(
    hass: HomeAssistant, monkeypatch
) -> None:
    """A slider step is rescaled into the mode the Z21 reports, then sent in it.

    Köf's slider is 0..14, but the station reports 128. Step 7/14 must go out
    as 63/126 in 128-step mode — sending it as 14 would store that mode (§4.2)
    and the decoder would ignore the speed change.
    """
    transport = await _setup(hass, monkeypatch)
    await _feed(hass, transport, address=7, forward=True, step=100, speed_steps=128)
    entity_id = _entity_id(hass, "number", 7, "speed")
    transport.sent.clear()

    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 7}, blocking=True
    )

    assert transport.sent == [_drive(7, step=63, forward=True, speed_steps=128)]


# --- Device removal ---------------------------------------------------------


async def test_only_stale_loco_devices_are_removable(
    hass: HomeAssistant, monkeypatch
) -> None:
    """A deleted loco's Device may be removed; the station and live locos not."""
    from custom_components.z21 import async_remove_config_entry_device

    await _setup(hass, monkeypatch)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    dev_reg = dr.async_get(hass)
    devices = {
        next(iter(dev.identifiers))[1]: dev
        for dev in dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
    }
    stale = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{_SERIAL}_loco_loco-deleted")},
        name="Deleted loco",
    )

    assert not await async_remove_config_entry_device(
        hass, entry, devices[str(_SERIAL)]
    )
    assert not await async_remove_config_entry_device(
        hass, entry, devices[f"{_SERIAL}_loco_loco-br218"]
    )
    assert await async_remove_config_entry_device(hass, entry, stale)


# --- Locos in motion (station-level) ----------------------------------------


def _moving_entity_id(hass: HomeAssistant) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        "binary_sensor", DOMAIN, f"{_SERIAL}_locos_moving"
    )


async def test_locos_moving_sits_on_the_station_device(
    hass: HomeAssistant, monkeypatch
) -> None:
    """The aggregate sensor is a ``moving`` binary sensor on the Z21 Device."""
    await _setup(hass, monkeypatch)

    entity_id = _moving_entity_id(hass)
    assert entity_id is not None
    entry_id = hass.config_entries.async_entries(DOMAIN)[0].entry_id
    station = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, str(_SERIAL)), entry_id
    )
    assert er.async_get(hass).async_get(entity_id).device_id == station.id
    state = hass.states.get(entity_id)
    assert state.attributes.get("device_class") == "moving"
    # No loco feedback yet -> unknown.
    assert state.state == "unknown"


async def test_locos_moving_follows_any_loco_speed(
    hass: HomeAssistant, monkeypatch
) -> None:
    """On while at least one loco reports speed > 0; off once all stand still."""
    transport = await _setup(hass, monkeypatch)
    entity_id = _moving_entity_id(hass)

    await _feed(hass, transport, address=3, forward=True, step=0, speed_steps=128)
    assert hass.states.get(entity_id).state == "off"

    await _feed(hass, transport, address=300, forward=False, step=10, speed_steps=28)
    assert hass.states.get(entity_id).state == "on"

    await _feed(hass, transport, address=3, forward=True, step=50, speed_steps=128)
    await _feed(hass, transport, address=300, forward=False, step=0, speed_steps=28)
    assert hass.states.get(entity_id).state == "on"

    await _feed(
        hass, transport, address=3, forward=True, step=0, speed_steps=128, estop=True
    )
    assert hass.states.get(entity_id).state == "off"


async def test_locos_moving_ignores_unconfigured_addresses(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Feedback for an address that is not a configured loco doesn't count."""
    transport = await _setup(hass, monkeypatch)
    entity_id = _moving_entity_id(hass)

    await _feed(hass, transport, address=3, forward=True, step=0, speed_steps=128)
    await _feed(hass, transport, address=42, forward=True, step=20, speed_steps=128)
    assert hass.states.get(entity_id).state == "off"


async def test_locos_moving_absent_without_locos(
    hass: HomeAssistant, monkeypatch
) -> None:
    """With no locos configured the aggregate sensor is not created."""
    _install_client(monkeypatch)
    entry = _mock_entry(locos=[])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert _moving_entity_id(hass) is None
