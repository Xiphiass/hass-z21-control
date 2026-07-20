"""Sensor platform for the Z21 integration.

v1 ships the six electrical-telemetry sensors carried by the System State push
(spec 2.18): main-track current, filtered main-track current, and
programming-track current (device_class ``current``, mA); internal temperature
(``temperature``, °C); supply voltage and track voltage (``voltage``, mV). All
read raw ints from the decoded ``SystemState`` — the wire values are already in
mA / °C / mV, so no scaling is applied. The entity list is description-driven so
further telemetry is additive later.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import protocol
from .const import CONF_SERIAL, DOMAIN
from .coordinator import Z21Coordinator


@dataclass(frozen=True, kw_only=True)
class Z21SensorDescription(SensorEntityDescription):
    """Describes a Z21 sensor and how to read it from System State."""

    # Returns the entity's native value from a System State snapshot.
    value_fn: Callable[[protocol.SystemState], int]


SENSORS: tuple[Z21SensorDescription, ...] = (
    Z21SensorDescription(
        key="main_current",
        translation_key="main_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.main_current,
    ),
    Z21SensorDescription(
        key="filtered_main_current",
        translation_key="filtered_main_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.filtered_main_current,
    ),
    Z21SensorDescription(
        key="prog_current",
        translation_key="prog_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.prog_current,
    ),
    Z21SensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.temperature,
    ),
    Z21SensorDescription(
        key="supply_voltage",
        translation_key="supply_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.supply_voltage,
    ),
    Z21SensorDescription(
        key="track_voltage",
        translation_key="track_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        state_class=SensorStateClass.MEASUREMENT,
        # "Track voltage" is the VCC field of the System State (CONTEXT.md).
        value_fn=lambda state: state.vcc_voltage,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Z21 sensors from a config entry."""
    coordinator: Z21Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        Z21Sensor(coordinator, entry, description) for description in SENSORS
    )


class Z21Sensor(CoordinatorEntity[Z21Coordinator], SensorEntity):
    """An electrical-telemetry value exposed as a sensor."""

    entity_description: Z21SensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Z21Coordinator,
        entry: ConfigEntry,
        description: Z21SensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = entry.data[CONF_SERIAL]
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(serial))}
        )

    @property
    def native_value(self) -> int | None:
        """Return the value, or ``None`` before the first System State."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
