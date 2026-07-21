"""Button platform for the Z21 integration.

The second **control** surface: an emergency-stop button that sends
``LAN_X_SET_STOP`` (2.13), halting all locos while **leaving track voltage on**
(distinct from track-power-off). Per ADR-0002 the button is **fire-and-forget**:
there is no dedicated confirmation broadcast consumed — the existing
``emergency_stop`` binary sensor (from ``csEmergencyStop`` in System State) is
its feedback, and an active stop is cleared by turning the track-power switch
back on. The button is therefore stateless. The entity list is
description-driven, mirroring the switch and sensor platforms.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import Z21Client
from .const import CONF_SERIAL, DOMAIN
from .coordinator import Z21Coordinator


@dataclass(frozen=True, kw_only=True)
class Z21ButtonDescription(ButtonEntityDescription):
    """Describes a Z21 button: the command it sends when pressed."""

    # Send the command for a button press.
    press_fn: Callable[[Z21Client], None]


BUTTONS: tuple[Z21ButtonDescription, ...] = (
    Z21ButtonDescription(
        key="emergency_stop",
        translation_key="emergency_stop",
        # No device_class — HA's button classes (restart/update/identify) don't
        # fit; an explicit stop-style icon instead.
        icon="mdi:alert-octagon",
        press_fn=lambda client: client.emergency_stop(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Z21 buttons from a config entry."""
    coordinator: Z21Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        Z21Button(coordinator, entry, description) for description in BUTTONS
    )


class Z21Button(CoordinatorEntity[Z21Coordinator], ButtonEntity):
    """A station-wide control exposed as a momentary, stateless button."""

    entity_description: Z21ButtonDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Z21Coordinator,
        entry: ConfigEntry,
        description: Z21ButtonDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = entry.data[CONF_SERIAL]
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, str(serial))})

    async def async_press(self) -> None:
        """Send the command; feedback comes via System State, not an ACK."""
        self.entity_description.press_fn(self.coordinator.client)
