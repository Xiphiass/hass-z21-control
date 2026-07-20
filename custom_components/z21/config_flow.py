"""Config flow for the Z21 integration.

Lets a user add a Z21 from the UI by entering the host IP only (port is fixed at
21105). The flow validates by round-tripping ``LAN_GET_SERIAL_NUMBER`` +
``LAN_GET_HWINFO`` through the HA-agnostic :class:`Z21Client`, so a wrong or
unreachable IP fails fast instead of creating a dead entry. The 32-bit serial
becomes the config-entry ``unique_id`` (survives IP changes, blocks duplicates).
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST

from .client import Z21Client, Z21Timeout
from .const import CONF_FW_VERSION, CONF_HW_TYPE, CONF_SERIAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Short validation budget so the UI stays responsive (worst case ~2.3s). These
# are module-level so tests can shrink them; the library defaults (2.0/3/0.5)
# would be ~8s.
_CONNECT_TIMEOUT = 1.0
_CONNECT_RETRIES = 2
_CONNECT_BACKOFF = 0.3

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class Z21ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Z21."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial (and only) step: ask for the host IP."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            try:
                serial, hwinfo = await self._async_validate(host)
            except (Z21Timeout, OSError):
                # Unreachable/wrong IP, dropped datagrams, or a bogus host that
                # fails in the socket layer before any round-trip.
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - surface as a generic error
                _LOGGER.exception("Unexpected error validating Z21 at %s", host)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(serial.serial))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Z21 ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_SERIAL: serial.serial,
                        CONF_HW_TYPE: hwinfo.hw_type,
                        CONF_FW_VERSION: hwinfo.fw_version,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _async_validate(self, host: str):
        """Open a client, round-trip serial + hwinfo, then tear it down.

        Nothing is kept live from the flow — the coordinator opens its own
        client later. Returns ``(SerialNumber, HwInfo)`` or raises.
        """
        client = Z21Client(host)
        try:
            return await client.connect(
                timeout=_CONNECT_TIMEOUT,
                retries=_CONNECT_RETRIES,
                backoff=_CONNECT_BACKOFF,
            )
        finally:
            await client.close()
