"""Switch platform for the Z21 integration.

The first **control** surface: a track-power switch that toggles the layout's
track voltage via ``LAN_X_SET_TRACK_POWER_ON`` (2.6) / ``LAN_X_SET_TRACK_POWER_OFF``
(2.5). Per ADR-0002 the switch is **send-only and non-optimistic**: ``is_on``
derives from ``not track_voltage_off`` in the System State snapshot, so it also
reflects power changes made by other input devices (e.g. a multiMaus) or a short
circuit. Fire-once, no retry or reconciliation. The entity list is
description-driven, mirroring the sensor platforms.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import protocol
from .client import Z21Client
from .const import (
    CONF_SERIAL,
    CONF_TURNOUTS,
    CONF_TURNOUT_FADR,
    CONF_TURNOUT_NAME,
    DOMAIN,
)
from .coordinator import Z21Coordinator


@dataclass(kw_only=True)
class Z21SwitchDescription(SwitchEntityDescription):
    """Describes a Z21 switch: how to read its state and drive the client."""

    # Returns the entity's ``is_on`` value from a System State snapshot.
    is_on_fn: Callable[[protocol.SystemState], bool]
    # Send the command for the requested state (``True`` = on).
    set_fn: Callable[[Z21Client, bool], None]


SWITCHES: tuple[Z21SwitchDescription, ...] = (
    Z21SwitchDescription(
        key="track_power",
        translation_key="track_power",
        device_class=SwitchDeviceClass.SWITCH,
        is_on_fn=lambda state: not state.track_voltage_off,
        set_fn=lambda client, on: (
            client.set_track_power_on() if on else client.set_track_power_off()
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Z21 switches from a config entry."""
    coordinator: Z21Coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[Z21Switch | Z21TurnoutSwitch] = [
        Z21Switch(coordinator, entry, description) for description in SWITCHES
    ]
    # Add turnout switches from configured turnouts
    for turnout in entry.options.get(CONF_TURNOUTS, []):
        entities.append(
            Z21TurnoutSwitch(
                coordinator=coordinator,
                entry=entry,
                fadr=turnout[CONF_TURNOUT_FADR],
                name=turnout[CONF_TURNOUT_NAME],
            )
        )
    async_add_entities(entities)


class Z21Switch(CoordinatorEntity[Z21Coordinator], SwitchEntity):
    """A station-wide control exposed as a switch (non-optimistic)."""

    entity_description: Z21SwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Z21Coordinator,
        entry: ConfigEntry,
        description: Z21SwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = entry.data[CONF_SERIAL]
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, str(serial))})

    @property
    def is_on(self) -> bool | None:
        """Return the state, or ``None`` before the first System State."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Send the power-on command; state follows the next System State."""
        self.entity_description.set_fn(self.coordinator.client, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Send the power-off command; state follows the next System State."""
        self.entity_description.set_fn(self.coordinator.client, False)


class Z21TurnoutSwitch(CoordinatorEntity[Z21Coordinator], SwitchEntity):
    """A turnout (Weiche) exposed as a switch entity.

    The Z21 protocol deliberately speaks only of "output 1" and "output 2", not
    "straight"/"branching" — the physical position depends on cabling the
    command station can't know (spec 5). Here ``on`` maps to output 2 and ``off``
    to output 1. ``is_on`` reflects the last known position (broadcast or poll);
    it is None (unknown) until the first position is reported. Each throw sends
    an Activate followed by a paired Deactivate — the client owns that timing.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Z21Coordinator,
        entry: ConfigEntry,
        fadr: int,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._fadr = fadr
        serial = entry.data[CONF_SERIAL]
        self._attr_unique_id = f"{serial}_turnout_{fadr}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, str(serial))})
        self._attr_name = name

    @property
    def is_on(self) -> bool | None:
        """Return the last known turnout position, or None if unknown."""
        pos = self.coordinator.turnout_positions.get(self._fadr)
        if pos is None:
            return None
        return pos == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch the turnout to output 2."""
        self.coordinator.client.set_turnout(self._fadr, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch the turnout to output 1."""
        self.coordinator.client.set_turnout(self._fadr, 0)

    async def async_added_to_hass(self) -> None:
        """Poll the initial position on entity creation."""
        await super().async_added_to_hass()
        self.coordinator.client.request_turnout_info(self._fadr)