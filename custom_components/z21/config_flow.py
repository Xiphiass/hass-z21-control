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
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)
from homeassistant.util.uuid import random_uuid_hex

from .client import Z21Client, Z21Timeout
from .const import (
    CONF_FW_VERSION,
    CONF_HW_TYPE,
    CONF_SERIAL,
    CONF_TURNOUT_FADR,
    CONF_TURNOUT_ID,
    CONF_TURNOUT_INVERTED,
    CONF_TURNOUT_NAME,
    CONF_TURNOUTS,
    DOMAIN,
    TURNOUT_FADR_MAX,
    TURNOUT_FADR_MIN,
)

_LOGGER = logging.getLogger(__name__)

# Short validation budget so the UI stays responsive (worst case ~2.3s). These
# are module-level so tests can shrink them; the library defaults (2.0/3/0.5)
# would be ~8s.
_CONNECT_TIMEOUT = 1.0
_CONNECT_RETRIES = 2
_CONNECT_BACKOFF = 0.3

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})

# Add/edit form: a friendly name plus the numeric function address. The address
# range is enforced by the NumberSelector; FAdr uniqueness needs the rest of the
# list, so it is checked in the handler and surfaced as ``duplicate_address``.
_TURNOUT_FORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TURNOUT_NAME): TextSelector(),
        vol.Required(CONF_TURNOUT_FADR): NumberSelector(
            NumberSelectorConfig(
                min=TURNOUT_FADR_MIN,
                max=TURNOUT_FADR_MAX,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(CONF_TURNOUT_INVERTED, default=False): BooleanSelector(),
    }
)


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
        return Z21OptionsFlow()


class Z21OptionsFlow(OptionsFlowWithReload):
    """Menu-driven turnout management for the Z21 config entry.

    Add / edit / delete turnouts from a menu that loops back after each action;
    ``Done`` commits the working list to ``entry.options`` and (via
    :class:`OptionsFlowWithReload`) schedules a single integration reload so the
    switch platform picks up the new set. Each turnout carries a stable ``id``
    independent of its FAdr, so it can be referenced across an address edit and
    its switch entity migrated to the new FAdr-based unique_id.
    """

    def __init__(self) -> None:
        # Lazily populated on the first init step from the live entry options.
        self._turnouts: list[dict] | None = None
        # id of the turnout currently being edited (set by edit_select).
        self._selected_id: str | None = None

    @property
    def _working(self) -> list[dict]:
        """The in-memory working copy of the turnout list.

        Loaded once from ``entry.options`` and backfilled with a stable ``id``
        for any legacy turnout that predates it; persisted only on ``Done``.
        """
        if self._turnouts is None:
            self._turnouts = [
                {**t, CONF_TURNOUT_ID: t.get(CONF_TURNOUT_ID) or random_uuid_hex()}
                for t in self.config_entry.options.get(CONF_TURNOUTS, [])
            ]
        return self._turnouts

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the turnout menu: add, edit/delete (if any), and done."""
        menu_options = ["add"]
        if self._working:
            menu_options += ["edit_select", "delete_select"]
        menu_options.append("done")
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    async def async_step_add(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new turnout, then return to the menu."""
        errors: dict[str, str] = {}
        if user_input is not None:
            error = self._validate_unique(user_input[CONF_TURNOUT_FADR])
            if error is None:
                self._working.append({
                    CONF_TURNOUT_ID: random_uuid_hex(),
                    CONF_TURNOUT_NAME: user_input[CONF_TURNOUT_NAME],
                    CONF_TURNOUT_FADR: int(user_input[CONF_TURNOUT_FADR]),
                    CONF_TURNOUT_INVERTED: user_input.get(
                        CONF_TURNOUT_INVERTED, False
                    ),
                })
                return await self.async_step_init()
            errors["base"] = error

        return self.async_show_form(
            step_id="add",
            data_schema=_TURNOUT_FORM_SCHEMA,
            errors=errors,
        )

    async def async_step_edit_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick which turnout to edit."""
        if not self._working:
            return await self.async_step_init()
        if user_input is not None:
            self._selected_id = user_input[CONF_TURNOUT_ID]
            return await self.async_step_edit()
        return self.async_show_form(
            step_id="edit_select",
            data_schema=self._select_schema(),
        )

    async def async_step_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit the selected turnout, then return to the menu."""
        turnout = self._find(self._selected_id)
        if turnout is None:
            return await self.async_step_init()

        errors: dict[str, str] = {}
        if user_input is not None:
            error = self._validate_unique(
                user_input[CONF_TURNOUT_FADR], exclude_id=self._selected_id
            )
            if error is None:
                turnout[CONF_TURNOUT_NAME] = user_input[CONF_TURNOUT_NAME]
                turnout[CONF_TURNOUT_FADR] = int(user_input[CONF_TURNOUT_FADR])
                turnout[CONF_TURNOUT_INVERTED] = user_input.get(
                    CONF_TURNOUT_INVERTED, False
                )
                return await self.async_step_init()
            errors["base"] = error

        return self.async_show_form(
            step_id="edit",
            data_schema=self.add_suggested_values_to_schema(
                _TURNOUT_FORM_SCHEMA,
                {
                    CONF_TURNOUT_NAME: turnout[CONF_TURNOUT_NAME],
                    CONF_TURNOUT_FADR: turnout[CONF_TURNOUT_FADR],
                    CONF_TURNOUT_INVERTED: turnout.get(
                        CONF_TURNOUT_INVERTED, False
                    ),
                },
            ),
            errors=errors,
        )

    async def async_step_delete_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick a turnout to delete, remove it, then return to the menu."""
        if not self._working:
            return await self.async_step_init()
        if user_input is not None:
            selected = user_input[CONF_TURNOUT_ID]
            self._turnouts = [
                t for t in self._working if t[CONF_TURNOUT_ID] != selected
            ]
            return await self.async_step_init()
        return self.async_show_form(
            step_id="delete_select",
            data_schema=self._select_schema(),
        )

    async def async_step_done(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Persist the working list and finish.

        If the meaningful turnout content (name + FAdr, in order) is unchanged,
        re-emit the stored options verbatim so Home Assistant sees no diff and
        :class:`OptionsFlowWithReload` skips the reload — a look-only session (or
        one that only backfilled internal ids) must not tear down the live Z21
        connection.
        """
        stored = self.config_entry.options
        if self._content(self._working) == self._content(
            stored.get(CONF_TURNOUTS, [])
        ):
            return self.async_create_entry(data=dict(stored))

        self._migrate_edited_entities()
        options = dict(stored)
        options[CONF_TURNOUTS] = self._working
        return self.async_create_entry(data=options)

    @staticmethod
    def _content(turnouts: list[dict]) -> list[tuple[str, int, bool]]:
        """The user-meaningful shape of a turnout list, ignoring internal ids."""
        return [
            (
                t[CONF_TURNOUT_NAME],
                int(t[CONF_TURNOUT_FADR]),
                bool(t.get(CONF_TURNOUT_INVERTED, False)),
            )
            for t in turnouts
        ]

    # --- Helpers -----------------------------------------------------------

    def _find(self, turnout_id: str | None) -> dict | None:
        """Return the working-list turnout with ``turnout_id``, or None."""
        return next(
            (t for t in self._working if t[CONF_TURNOUT_ID] == turnout_id), None
        )

    def _validate_unique(
        self, fadr: int | float, *, exclude_id: str | None = None
    ) -> str | None:
        """Return an error key if ``fadr`` collides with another turnout."""
        fadr = int(fadr)
        for t in self._working:
            if t[CONF_TURNOUT_ID] == exclude_id:
                continue
            if t[CONF_TURNOUT_FADR] == fadr:
                return "duplicate_address"
        return None

    def _select_schema(self) -> vol.Schema:
        """A one-field schema: a dropdown of turnouts labelled by name."""
        options = [
            {
                "value": t[CONF_TURNOUT_ID],
                "label": f"{t[CONF_TURNOUT_NAME]} (FAdr {t[CONF_TURNOUT_FADR]})",
            }
            for t in self._working
        ]
        return vol.Schema({
            vol.Required(CONF_TURNOUT_ID): SelectSelector(
                SelectSelectorConfig(
                    options=options, mode=SelectSelectorMode.DROPDOWN
                )
            )
        })

    def _migrate_edited_entities(self) -> None:
        """Carry each turnout's switch entity across an FAdr change.

        The switch unique_id is ``{serial}_turnout_{fadr}``; when a turnout keeps
        its stable id but changes FAdr, rename the existing registry entry so its
        history/area/customisations survive instead of orphaning as unavailable.

        Renames run in **two phases** so an address swap/shuffle can't collide:
        each entity being moved is first parked on a temporary unique_id, then
        settled on its target. A one-phase rename in list order would raise
        ``ValueError`` if a target unique_id is still held by another entity that
        is itself scheduled to move later in the batch.
        """
        original = {
            t[CONF_TURNOUT_ID]: t
            for t in self.config_entry.options.get(CONF_TURNOUTS, [])
            if CONF_TURNOUT_ID in t
        }
        serial = self.config_entry.data[CONF_SERIAL]
        registry = er.async_get(self.hass)

        def unique_id(fadr: int) -> str:
            return f"{serial}_turnout_{fadr}"

        # Collect the (entity_id -> target unique_id) moves for changed FAdrs.
        moves: list[tuple[str, str]] = []
        for t in self._working:
            old = original.get(t[CONF_TURNOUT_ID])
            if old is None or old[CONF_TURNOUT_FADR] == t[CONF_TURNOUT_FADR]:
                continue
            entity_id = registry.async_get_entity_id(
                "switch", DOMAIN, unique_id(old[CONF_TURNOUT_FADR])
            )
            if entity_id is not None:
                moves.append((entity_id, unique_id(t[CONF_TURNOUT_FADR])))

        # Phase 1: park each mover on a collision-proof temporary unique_id.
        for entity_id, _target in moves:
            registry.async_update_entity(
                entity_id, new_unique_id=f"migrating_{entity_id}"
            )
        # Phase 2: settle each on its target, now guaranteed free.
        for entity_id, target in moves:
            registry.async_update_entity(entity_id, new_unique_id=target)
