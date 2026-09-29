"""Shared base for the per-loco drive entities (ADR-0003).

Each configured loco is its own HA **Device**, nested under the Z21 station via
``via_device``, carrying a speed ``number``, a direction ``switch`` and an E-Stop
``button`` (CONTEXT.md "Loco entities"). The Device is keyed by the loco's stable
``id`` rather than its DCC address, so an address edit in the options flow keeps
the same Device; the entity unique_ids are address-based
(``{serial}_loco_{address}_{suffix}``) and migrated by the options flow. Leaving
room for function entities later means they only need to subclass this.

All three entities are **non-optimistic**: state derives from the coordinator's
last-known ``LocoInfo`` for the address (``None`` until the first feedback), so
external control from a handset or another app is reflected in HA.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import protocol
from .const import (
    CONF_LOCO_ADDRESS,
    CONF_LOCO_ID,
    CONF_LOCO_NAME,
    CONF_LOCO_SPEED_STEPS,
    CONF_SERIAL,
    DOMAIN,
    LOCO_SPEED_STEPS_DEFAULT,
)
from .coordinator import Z21Coordinator


def loco_device_identifier(serial: int, loco: dict) -> tuple[str, str]:
    """Return the device-registry identifier of a configured loco's Device.

    Keyed by the stable loco ``id`` when present (the options flow always assigns
    one); a hand-written entry lacking it falls back to the address.
    """
    loco_key = loco.get(CONF_LOCO_ID) or f"address_{loco[CONF_LOCO_ADDRESS]}"
    return (DOMAIN, f"{serial}_loco_{loco_key}")


class Z21LocoEntity(CoordinatorEntity[Z21Coordinator]):
    """A drive entity belonging to one configured loco's Device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Z21Coordinator,
        entry: ConfigEntry,
        loco: dict,
        suffix: str,
    ) -> None:
        super().__init__(coordinator)
        serial = entry.data[CONF_SERIAL]
        self._address: int = loco[CONF_LOCO_ADDRESS]
        self._speed_steps: int = loco.get(
            CONF_LOCO_SPEED_STEPS, LOCO_SPEED_STEPS_DEFAULT
        )
        self._attr_unique_id = f"{serial}_loco_{self._address}_{suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={loco_device_identifier(serial, loco)},
            name=loco[CONF_LOCO_NAME],
            via_device=(DOMAIN, str(serial)),
        )

    @property
    def _info(self) -> protocol.LocoInfo | None:
        """The loco's last reported ``LAN_X_LOCO_INFO``, or ``None`` if none yet."""
        return self.coordinator.loco_states.get(self._address)
