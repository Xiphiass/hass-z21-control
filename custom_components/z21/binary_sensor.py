"""Binary sensor platform for the Z21 integration.

The Central State flags from the System State push (spec 2.18) exposed as binary
sensors. **Track voltage off** uses device_class ``power`` with inverted
semantics so HA shows *on = track powered*. The operational-fault flags
(emergency stop, short circuit, over-temperature, power lost) use device_class
``problem`` with straight semantics (*on = fault*); programming-mode-active is a
diagnostic sensor with no device_class. The entity list is description-driven, so
adding a flag is a single tuple entry.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import protocol
from .const import CONF_SERIAL, DOMAIN
from .coordinator import Z21Coordinator


@dataclass(frozen=True, kw_only=True)
class Z21BinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Z21 binary sensor and how to read it from System State."""

    # Returns the entity's ``is_on`` value from a System State snapshot.
    is_on_fn: Callable[[protocol.SystemState], bool]


BINARY_SENSORS: tuple[Z21BinarySensorDescription, ...] = (
    Z21BinarySensorDescription(
        key="track_voltage_off",
        translation_key="track_voltage_off",
        device_class=BinarySensorDeviceClass.POWER,
        # Inverted: on = track powered, off = track voltage off.
        is_on_fn=lambda state: not state.track_voltage_off,
    ),
    Z21BinarySensorDescription(
        key="emergency_stop",
        translation_key="emergency_stop",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda state: state.emergency_stop,
    ),
    Z21BinarySensorDescription(
        key="short_circuit",
        translation_key="short_circuit",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda state: state.short_circuit,
    ),
    Z21BinarySensorDescription(
        key="over_temperature",
        translation_key="over_temperature",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda state: state.high_temperature,
    ),
    Z21BinarySensorDescription(
        key="power_lost",
        translation_key="power_lost",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda state: state.power_lost,
    ),
    Z21BinarySensorDescription(
        key="programming_mode",
        translation_key="programming_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda state: state.programming_mode_active,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Z21 binary sensors from a config entry."""
    coordinator: Z21Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        Z21BinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class Z21BinarySensor(CoordinatorEntity[Z21Coordinator], BinarySensorEntity):
    """A Central State flag exposed as a binary sensor."""

    entity_description: Z21BinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Z21Coordinator,
        entry: ConfigEntry,
        description: Z21BinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = entry.data[CONF_SERIAL]
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(serial))}
        )

    @property
    def is_on(self) -> bool | None:
        """Return the flag value, or ``None`` before the first System State."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.is_on_fn(self.coordinator.data)
