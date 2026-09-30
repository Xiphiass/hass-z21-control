"""Loco function entity tests for the Z21 integration.

Each function configured on a loco becomes either a latching ``switch`` (state
follows the function bit of ``LAN_X_LOCO_INFO``, non-optimistic) or a momentary
``button`` (on, then off after a pulse) on that loco's Device. Both send
``LAN_X_SET_LOCO_FUNCTION`` (4.3.1). Reuses the fakes of
``test_loco_entities.py``.
"""

from __future__ import annotations

import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.z21 import client as client_mod, protocol
from custom_components.z21.const import (
    CONF_FUNCTION_ID,
    CONF_FUNCTION_NAME,
    CONF_FUNCTION_NUMBER,
    CONF_FUNCTION_TYPE,
    CONF_LOCO_ADDRESS,
    CONF_LOCO_FUNCTIONS,
    CONF_LOCO_ID,
    CONF_LOCO_NAME,
    CONF_LOCO_SPEED_STEPS,
    DOMAIN,
)
from tests.test_loco_entities import (
    _SERIAL,
    _entity_id,
    _feed,
    _install_client,
    _mock_entry,
)

_LOCOS = [
    {
        CONF_LOCO_ID: "loco-br218",
        CONF_LOCO_NAME: "BR 218",
        CONF_LOCO_ADDRESS: 3,
        CONF_LOCO_SPEED_STEPS: 128,
        CONF_LOCO_FUNCTIONS: [
            {
                CONF_FUNCTION_ID: "f-light",
                CONF_FUNCTION_NAME: "Light",
                CONF_FUNCTION_NUMBER: 0,
                CONF_FUNCTION_TYPE: "switch",
            },
            {
                CONF_FUNCTION_ID: "f-horn",
                CONF_FUNCTION_NAME: "Horn",
                CONF_FUNCTION_NUMBER: 2,
                CONF_FUNCTION_TYPE: "button",
            },
            {
                CONF_FUNCTION_ID: "f-smoke",
                CONF_FUNCTION_NAME: "Smoke",
                CONF_FUNCTION_NUMBER: 31,
                CONF_FUNCTION_TYPE: "switch",
            },
        ],
    },
    # A loco configured before functions existed: no functions key at all.
    {
        CONF_LOCO_ID: "loco-v100",
        CONF_LOCO_NAME: "V 100",
        CONF_LOCO_ADDRESS: 300,
        CONF_LOCO_SPEED_STEPS: 28,
    },
]


async def _setup(hass: HomeAssistant, monkeypatch):
    transports = _install_client(monkeypatch)
    entry = _mock_entry(_LOCOS)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return transports[0]


async def test_function_entities_by_type_on_the_loco_device(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Switch functions are switches, button functions buttons, named by config."""
    await _setup(hass, monkeypatch)
    registry = er.async_get(hass)

    light = _entity_id(hass, "switch", 3, "f0")
    horn = _entity_id(hass, "button", 3, "f2")
    speed = _entity_id(hass, "number", 3, "speed")
    assert registry.async_get(light).device_id == registry.async_get(speed).device_id
    assert registry.async_get(horn).device_id == registry.async_get(speed).device_id
    assert hass.states.get(light).attributes["friendly_name"] == "BR 218 Light"
    assert hass.states.get(horn).attributes["friendly_name"] == "BR 218 Horn"

    # Each function lives only on the platform of its type.
    assert registry.async_get_entity_id("button", DOMAIN, f"{_SERIAL}_loco_3_f0") is None
    assert registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_loco_3_f2") is None


async def test_function_switch_follows_reported_bits(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Unknown until function bits are reported, then follows them (incl. F31)."""
    transport = await _setup(hass, monkeypatch)
    light = _entity_id(hass, "switch", 3, "f0")
    smoke = _entity_id(hass, "switch", 3, "f31")
    assert hass.states.get(light).state == "unknown"

    # Feedback without function bytes leaves the state unknown.
    await _feed(hass, transport, address=3, forward=True, step=0, speed_steps=128)
    assert hass.states.get(light).state == "unknown"

    await _feed(hass, transport, address=3, forward=True, step=0, speed_steps=128,
                functions=1 << 0)
    assert hass.states.get(light).state == "on"
    assert hass.states.get(smoke).state == "off"

    # A handset switches F0 off and F31 on: HA follows.
    await _feed(hass, transport, address=3, forward=True, step=0, speed_steps=128,
                functions=1 << 31)
    assert hass.states.get(light).state == "off"
    assert hass.states.get(smoke).state == "on"


async def test_function_switch_sends_set_function_non_optimistically(
    hass: HomeAssistant, monkeypatch
) -> None:
    transport = await _setup(hass, monkeypatch)
    await _feed(hass, transport, address=3, forward=True, step=0, speed_steps=128,
                functions=0)
    light = _entity_id(hass, "switch", 3, "f0")
    transport.sent.clear()

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": light}, blocking=True
    )
    assert transport.sent == [protocol.build_loco_function(3, 0, on=True)]
    # Non-optimistic: still off until the Z21 echoes the change.
    assert hass.states.get(light).state == "off"

    transport.sent.clear()
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": light}, blocking=True
    )
    assert transport.sent == [protocol.build_loco_function(3, 0, on=False)]


async def test_function_button_pulses_on_then_off(
    hass: HomeAssistant, monkeypatch
) -> None:
    monkeypatch.setattr(client_mod, "LOCO_FUNCTION_PULSE", 0.01)
    transport = await _setup(hass, monkeypatch)
    horn = _entity_id(hass, "button", 3, "f2")
    transport.sent.clear()

    await hass.services.async_call(
        "button", "press", {"entity_id": horn}, blocking=True
    )
    assert transport.sent == [protocol.build_loco_function(3, 2, on=True)]

    await asyncio.sleep(0.05)
    assert transport.sent == [
        protocol.build_loco_function(3, 2, on=True),
        protocol.build_loco_function(3, 2, on=False),
    ]


async def test_loco_without_functions_has_no_function_entities(
    hass: HomeAssistant, monkeypatch
) -> None:
    await _setup(hass, monkeypatch)
    registry = er.async_get(hass)
    unique_ids = {
        entry.unique_id
        for entry in registry.entities.values()
        if entry.unique_id.startswith(f"{_SERIAL}_loco_300_")
    }
    assert unique_ids == {
        f"{_SERIAL}_loco_300_speed",
        f"{_SERIAL}_loco_300_direction",
        f"{_SERIAL}_loco_300_estop",
    }
