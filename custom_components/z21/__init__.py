"""Z21 command station integration for Home Assistant.

v1 is monitor-only: setup opens a live :class:`Z21Client`, registers the Z21 as a
single HA Device, and runs a System State coordinator that feeds the binary
sensor platform. Control commands land in later issues on the same I/O seam.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .client import Z21Client
from .const import (
    CONF_FW_VERSION,
    CONF_HW_TYPE,
    CONF_SERIAL,
    DOMAIN,
    MANUFACTURER,
    format_fw_version,
    hw_type_name,
)
from .coordinator import Z21Coordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Register the Z21 Device, start the coordinator, and forward platforms.

    Hardware type and firmware version were captured by the config flow, so the
    Device is registered from entry data. The coordinator then opens the live
    client and performs the handshake; if no System State arrives it raises
    ``ConfigEntryNotReady`` and HA retries.
    """
    serial = entry.data[CONF_SERIAL]
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, str(serial))},
        manufacturer=MANUFACTURER,
        name=entry.title,
        model=hw_type_name(entry.data[CONF_HW_TYPE]),
        sw_version=format_fw_version(entry.data[CONF_FW_VERSION]),
    )

    coordinator = Z21Coordinator(hass, entry, Z21Client(entry.data[CONF_HOST]))
    await coordinator.async_setup()
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        # First refresh raised ConfigEntryNotReady (or worse) — don't leak the
        # open socket while HA waits to retry.
        await coordinator.async_shutdown_client()
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry: tear down platforms and close the live client."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator: Z21Coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown_client()
    return unloaded
