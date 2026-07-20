"""Z21 command station integration for Home Assistant.

v1 registers the Z21 as a single HA Device from the config entry. The
coordinator and entity platforms (System State sensors/binary sensors) land in
later issues; setup here does not yet open a live client.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_FW_VERSION,
    CONF_HW_TYPE,
    CONF_SERIAL,
    DOMAIN,
    MANUFACTURER,
    format_fw_version,
    hw_type_name,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Register the Z21 Device from the config entry data.

    Hardware type and firmware version were captured by the config flow, so no
    connection is opened here — the coordinator (later issue) owns the live
    client.
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
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Nothing to tear down until platforms/coordinator exist; the device registry
    entry is removed automatically when the config entry is deleted.
    """
    return True
