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
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    FlowResult,
    OptionsFlow,
)
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

# Turnout config constants
TURNOUT_FADR_MIN = 0
TURNOUT_FADR_MAX = 65534
CONF_TURNOUTS = "turnouts"
CONF_TURNOUT_NAME = "name"
CONF_TURNOUT_FADR = "fadr"
CONF_TURNOUT_Q_MODE = "q_mode"


def _validate_turnout_fadr_uniqueness(turnouts: list[dict]) -> list[dict]:
    """Validate that FAdr values are unique across all turnouts."""
    seen_fadr: dict[int, str] = {}
    for t in turnouts:
        fadr = t[CONF_TURNOUT_FADR]
        if fadr in seen_fadr:
            raise vol.Invalid(
                f"Duplicate FAdr {fadr} (used by '{seen_fadr[fadr]}')",
                path=[CONF_TURNOUTS],
            )
        seen_fadr[fadr] = t[CONF_TURNOUT_NAME]
    return turnouts


# Form schema: permissive (no range constraint) so HA's async_configure
# doesn't raise before the handler can catch the error.
TURNOUT_ITEM_SCHEMA = vol.Schema({
    vol.Required(CONF_TURNOUT_NAME): str,
    vol.Required(CONF_TURNOUT_FADR): vol.Coerce(int),
    vol.Optional(CONF_TURNOUT_Q_MODE, default=0): vol.Coerce(int),
})

# Full validation schema with range + uniqueness checks.
TURNOUT_SCHEMA = vol.Schema(
    vol.All(
        [TURNOUT_ITEM_SCHEMA],
        vol.All(
            vol.Range(min=TURNOUT_FADR_MIN, max=TURNOUT_FADR_MAX),
            _validate_turnout_fadr_uniqueness,
        ),
    )
)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class Z21ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Z21."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> Z21OptionsFlow:
        """Get the options flow for this config entry."""
        return Z21OptionsFlow(config_entry)


class Z21OptionsFlow(OptionsFlow):
    """Handle options for the Z21 config entry."""

    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry
        self._turnouts: list[dict] = list(entry.options.get(CONF_TURNOUTS, []))
        self._edit_index: int | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the list of configured turnouts with add/edit/delete actions."""
        if user_input is not None:
            if "action" in user_input:
                action = user_input["action"]
                if action == "add":
                    return await self.async_step_add_turnout()
                if action.startswith("edit_"):
                    idx = int(action.replace("edit_", ""))
                    self._edit_index = idx
                    return await self.async_step_edit_turnout()
                if action.startswith("delete_"):
                    idx = int(action.replace("delete_", ""))
                    self._turnouts.pop(idx)
                    return await self.async_step_init()
            # Empty submission - save current state
            self.hass.config_entries.async_update_entry(
                self.entry,
                options={CONF_TURNOUTS: self._turnouts},
            )
            return self.async_create_entry(data=self._save_options())

        items: list[str] = []
        for i, t in enumerate(self._turnouts):
            label = f"{t[CONF_TURNOUT_NAME]} (FAdr {t[CONF_TURNOUT_FADR]})"
            items.append(f"{i}. {label}")
        if not items:
            items.append("No turnouts configured.")

        actions: list[str] = ["add"]
        for i in range(len(self._turnouts)):
            actions.append(f"edit_{i}")
            actions.append(f"delete_{i}")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("action"): vol.In(actions),
            }),
            description_placeholders={"turnouts": "\n".join(items)},
        )

    async def async_step_add_turnout(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new turnout."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # Validate range first
                fadr = user_input[CONF_TURNOUT_FADR]
                if fadr < TURNOUT_FADR_MIN or fadr > TURNOUT_FADR_MAX:
                    raise vol.Invalid(
                        f"FAdr must be between {TURNOUT_FADR_MIN} and {TURNOUT_FADR_MAX}",
                        path=[CONF_TURNOUT_FADR],
                    )
                # Validate uniqueness
                test_list = list(self._turnouts) + [user_input]
                _validate_turnout_fadr_uniqueness(test_list)
                self._turnouts.append(user_input)
                return self.async_create_entry(data=self._save_options())
            except vol.Invalid as err:
                errors["base"] = str(err)

        return self.async_show_form(
            step_id="add_turnout",
            data_schema=TURNOUT_ITEM_SCHEMA,
            errors=errors,
        )

    async def async_step_edit_turnout(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit an existing turnout."""
        errors: dict[str, str] = {}
        if self._edit_index is None:
            return await self.async_step_init()

        current = self._turnouts[self._edit_index]

        if user_input is not None:
            try:
                # Validate range first
                fadr = user_input[CONF_TURNOUT_FADR]
                if fadr < TURNOUT_FADR_MIN or fadr > TURNOUT_FADR_MAX:
                    raise vol.Invalid(
                        f"FAdr must be between {TURNOUT_FADR_MIN} and {TURNOUT_FADR_MAX}",
                        path=[CONF_TURNOUT_FADR],
                    )
                # Build full list with edited item, validate uniqueness across all
                test_list = list(self._turnouts)
                test_list[self._edit_index] = user_input
                _validate_turnout_fadr_uniqueness(test_list)
                self._turnouts[self._edit_index] = user_input
                return self.async_create_entry(data=self._save_options())
            except vol.Invalid as err:
                errors["base"] = str(err)

        schema = vol.Schema({
            vol.Required(CONF_TURNOUT_NAME, default=current[CONF_TURNOUT_NAME]): str,
            vol.Required(CONF_TURNOUT_FADR, default=current[CONF_TURNOUT_FADR]): vol.Coerce(int),
            vol.Optional(CONF_TURNOUT_Q_MODE, default=current.get(CONF_TURNOUT_Q_MODE, 0)): vol.Coerce(int),
        })

        return self.async_show_form(
            step_id="edit_turnout",
            data_schema=schema,
            errors=errors,
        )

    def _save_options(self) -> dict[str, Any]:
        """Build the options dict from the current turnout list."""
        data: dict[str, Any] = dict(self.entry.options)
        data[CONF_TURNOUTS] = self._turnouts
        return data