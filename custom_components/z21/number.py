"""Number platform for the Z21 integration: per-loco speed.

Each configured loco gets a speed ``number`` in **raw DCC steps** — 0..14,
0..28 or 0..126 for its configured 14 / 28 / 128 step mode — so the
``LAN_X_LOCO_INFO`` echo round-trips without rounding (CONTEXT.md "Locos").
Setting a value sends ``LAN_X_SET_LOCO_DRIVE`` (4.2) composed with the loco's
last-known direction, in the step mode the Z21 last reported — the slider value
is rescaled into that mode so the command does not rewrite the address's stored
mode (ADR-0003). 0 is a normal **Stop**, never the E-Stop (that is the loco's
``button``). Per ADR-0003 the entity is **non-optimistic**: its value follows
the Z21's feedback, and a reported step above the slider max (a configured step
mode disagreeing with the Z21's) is clamped and logged.
"""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import protocol
from .const import CONF_LOCOS, DOMAIN
from .coordinator import Z21Coordinator
from .entity import Z21LocoEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one speed number per configured loco."""
    coordinator: Z21Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        Z21LocoSpeed(coordinator, entry, loco)
        for loco in entry.options.get(CONF_LOCOS, [])
    )


class Z21LocoSpeed(Z21LocoEntity, NumberEntity):
    """A loco's speed in raw DCC steps (non-optimistic)."""

    _attr_translation_key = "speed"
    _attr_icon = "mdi:speedometer"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_step = 1

    def __init__(
        self, coordinator: Z21Coordinator, entry: ConfigEntry, loco: dict
    ) -> None:
        super().__init__(coordinator, entry, loco, "speed")
        # 128-step mode has 126 drivable steps (plus Stop / E-Stop codes).
        self._attr_native_max_value = protocol.max_speed_step(self._speed_steps)
        # Last out-of-range step logged, so a steady report warns only once.
        self._clamped_from: int | None = None

    @property
    def native_value(self) -> int | None:
        """The reported step (0 on Stop/E-Stop), clamped to the slider max."""
        info = self._info
        if info is None:
            return None
        maximum = int(self._attr_native_max_value)
        if info.speed <= maximum:
            self._clamped_from = None
            return info.speed
        if info.speed != self._clamped_from:
            self._clamped_from = info.speed
            _LOGGER.warning(
                "Loco %s reported speed step %s above the %s-step maximum %s "
                "(Z21 reports %s-step mode); clamping",
                self._address,
                info.speed,
                self._speed_steps,
                maximum,
                info.speed_steps,
            )
        return maximum

    async def async_set_native_value(self, value: float) -> None:
        """Send the new speed at the last-known direction; state follows feedback."""
        self.coordinator.drive_loco(self._address, speed=int(value))
