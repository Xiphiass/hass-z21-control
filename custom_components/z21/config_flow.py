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
    CONF_LOCO_ADDRESS,
    CONF_LOCO_ID,
    CONF_LOCO_NAME,
    CONF_LOCO_SPEED_STEPS,
    CONF_LOCOS,
    CONF_SERIAL,
    CONF_TURNOUT_FADR,
    CONF_TURNOUT_ID,
    CONF_TURNOUT_INVERTED,
    CONF_TURNOUT_NAME,
    CONF_TURNOUTS,
    DOMAIN,
    LOCO_ADDRESS_MAX,
    LOCO_ADDRESS_MIN,
    LOCO_MAX,
    LOCO_SPEED_STEPS,
    LOCO_SPEED_STEPS_DEFAULT,
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

# Add/edit form for a loco: a friendly name, the DCC address, and a speed-step
# mode. The address range is enforced by the NumberSelector; uniqueness and the
# 16-loco cap need the rest of the list, so they are checked in the handler and
# surfaced as ``duplicate_address`` / ``too_many_locos``. DCC only — the step
# mode is stored per loco (the drive command requires it) but no
# ``LAN_SET_LOCOMODE`` is ever sent.
_LOCO_FORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LOCO_NAME): TextSelector(),
        vol.Required(CONF_LOCO_ADDRESS): NumberSelector(
            NumberSelectorConfig(
                min=LOCO_ADDRESS_MIN,
                max=LOCO_ADDRESS_MAX,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        ),
        vol.Required(
            CONF_LOCO_SPEED_STEPS, default=str(LOCO_SPEED_STEPS_DEFAULT)
        ): SelectSelector(
            SelectSelectorConfig(
                options=[str(s) for s in LOCO_SPEED_STEPS],
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
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
    """Menu-driven hardware management for the Z21 config entry.

    A top-level menu branches into turnout management and loco management, so all
    hand-configured hardware lives in one place, then ``Done`` commits both
    working lists to ``entry.options`` and (via :class:`OptionsFlowWithReload`)
    schedules a single integration reload so the entity platforms pick up the new
    sets. Each turnout/loco carries a stable ``id`` independent of its address, so
    it can be referenced across an address edit and its entities migrated to the
    new address-based unique_id.
    """

    def __init__(self) -> None:
        # Lazily populated on first access from the live entry options.
        self._turnouts: list[dict] | None = None
        self._locos: list[dict] | None = None
        # id of the item currently being edited (set by *_edit_select).
        self._selected_id: str | None = None

    @property
    def _turnout_working(self) -> list[dict]:
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

    @property
    def _loco_working(self) -> list[dict]:
        """The in-memory working copy of the loco list.

        Loaded once from ``entry.options`` and backfilled with a stable ``id``
        for any loco that predates it; persisted only on ``Done``.
        """
        if self._locos is None:
            self._locos = [
                {**l, CONF_LOCO_ID: l.get(CONF_LOCO_ID) or random_uuid_hex()}
                for l in self.config_entry.options.get(CONF_LOCOS, [])
            ]
        return self._locos

    # --- Top-level menu ----------------------------------------------------

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the top-level menu: manage turnouts, manage locos, done."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["manage_turnouts", "manage_locos", "done"],
        )

    # --- Turnout management ------------------------------------------------

    async def async_step_manage_turnouts(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the turnout submenu: add, edit/delete (if any), and back."""
        menu_options = ["turnout_add"]
        if self._turnout_working:
            menu_options += ["turnout_edit_select", "turnout_delete_select"]
        menu_options.append("init")
        return self.async_show_menu(
            step_id="manage_turnouts", menu_options=menu_options
        )

    async def async_step_turnout_add(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new turnout, then return to the turnout submenu."""
        errors: dict[str, str] = {}
        if user_input is not None:
            error = self._validate_turnout_unique(user_input[CONF_TURNOUT_FADR])
            if error is None:
                self._turnout_working.append({
                    CONF_TURNOUT_ID: random_uuid_hex(),
                    CONF_TURNOUT_NAME: user_input[CONF_TURNOUT_NAME],
                    CONF_TURNOUT_FADR: int(user_input[CONF_TURNOUT_FADR]),
                    CONF_TURNOUT_INVERTED: user_input.get(
                        CONF_TURNOUT_INVERTED, False
                    ),
                })
                return await self.async_step_manage_turnouts()
            errors["base"] = error

        return self.async_show_form(
            step_id="turnout_add",
            data_schema=_TURNOUT_FORM_SCHEMA,
            errors=errors,
        )

    async def async_step_turnout_edit_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick which turnout to edit."""
        if not self._turnout_working:
            return await self.async_step_manage_turnouts()
        if user_input is not None:
            self._selected_id = user_input[CONF_TURNOUT_ID]
            return await self.async_step_turnout_edit()
        return self.async_show_form(
            step_id="turnout_edit_select",
            data_schema=self._turnout_select_schema(),
        )

    async def async_step_turnout_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit the selected turnout, then return to the turnout submenu."""
        turnout = self._find(self._turnout_working, self._selected_id)
        if turnout is None:
            return await self.async_step_manage_turnouts()

        errors: dict[str, str] = {}
        if user_input is not None:
            error = self._validate_turnout_unique(
                user_input[CONF_TURNOUT_FADR], exclude_id=self._selected_id
            )
            if error is None:
                turnout[CONF_TURNOUT_NAME] = user_input[CONF_TURNOUT_NAME]
                turnout[CONF_TURNOUT_FADR] = int(user_input[CONF_TURNOUT_FADR])
                turnout[CONF_TURNOUT_INVERTED] = user_input.get(
                    CONF_TURNOUT_INVERTED, False
                )
                return await self.async_step_manage_turnouts()
            errors["base"] = error

        return self.async_show_form(
            step_id="turnout_edit",
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

    async def async_step_turnout_delete_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick a turnout to delete, remove it, then return to the submenu."""
        if not self._turnout_working:
            return await self.async_step_manage_turnouts()
        if user_input is not None:
            selected = user_input[CONF_TURNOUT_ID]
            self._turnouts = [
                t for t in self._turnout_working if t[CONF_TURNOUT_ID] != selected
            ]
            return await self.async_step_manage_turnouts()
        return self.async_show_form(
            step_id="turnout_delete_select",
            data_schema=self._turnout_select_schema(),
        )

    # --- Loco management ---------------------------------------------------

    async def async_step_manage_locos(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the loco submenu: add, edit/delete (if any), and back."""
        menu_options = ["loco_add"]
        if self._loco_working:
            menu_options += ["loco_edit_select", "loco_delete_select"]
        menu_options.append("init")
        return self.async_show_menu(
            step_id="manage_locos", menu_options=menu_options
        )

    async def async_step_loco_add(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new loco, then return to the loco submenu."""
        errors: dict[str, str] = {}
        if user_input is not None:
            error = self._validate_loco_add(user_input[CONF_LOCO_ADDRESS])
            if error is None:
                self._loco_working.append({
                    CONF_LOCO_ID: random_uuid_hex(),
                    CONF_LOCO_NAME: user_input[CONF_LOCO_NAME],
                    CONF_LOCO_ADDRESS: int(user_input[CONF_LOCO_ADDRESS]),
                    CONF_LOCO_SPEED_STEPS: int(user_input[CONF_LOCO_SPEED_STEPS]),
                })
                return await self.async_step_manage_locos()
            errors["base"] = error

        return self.async_show_form(
            step_id="loco_add",
            data_schema=_LOCO_FORM_SCHEMA,
            errors=errors,
        )

    async def async_step_loco_edit_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick which loco to edit."""
        if not self._loco_working:
            return await self.async_step_manage_locos()
        if user_input is not None:
            self._selected_id = user_input[CONF_LOCO_ID]
            return await self.async_step_loco_edit()
        return self.async_show_form(
            step_id="loco_edit_select",
            data_schema=self._loco_select_schema(),
        )

    async def async_step_loco_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit the selected loco, then return to the loco submenu."""
        loco = self._find(self._loco_working, self._selected_id)
        if loco is None:
            return await self.async_step_manage_locos()

        errors: dict[str, str] = {}
        if user_input is not None:
            error = self._validate_loco_unique(
                user_input[CONF_LOCO_ADDRESS], exclude_id=self._selected_id
            )
            if error is None:
                loco[CONF_LOCO_NAME] = user_input[CONF_LOCO_NAME]
                loco[CONF_LOCO_ADDRESS] = int(user_input[CONF_LOCO_ADDRESS])
                loco[CONF_LOCO_SPEED_STEPS] = int(
                    user_input[CONF_LOCO_SPEED_STEPS]
                )
                return await self.async_step_manage_locos()
            errors["base"] = error

        return self.async_show_form(
            step_id="loco_edit",
            data_schema=self.add_suggested_values_to_schema(
                _LOCO_FORM_SCHEMA,
                {
                    CONF_LOCO_NAME: loco[CONF_LOCO_NAME],
                    CONF_LOCO_ADDRESS: loco[CONF_LOCO_ADDRESS],
                    CONF_LOCO_SPEED_STEPS: str(loco[CONF_LOCO_SPEED_STEPS]),
                },
            ),
            errors=errors,
        )

    async def async_step_loco_delete_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick a loco to delete, remove it, then return to the submenu."""
        if not self._loco_working:
            return await self.async_step_manage_locos()
        if user_input is not None:
            selected = user_input[CONF_LOCO_ID]
            self._locos = [
                l for l in self._loco_working if l[CONF_LOCO_ID] != selected
            ]
            return await self.async_step_manage_locos()
        return self.async_show_form(
            step_id="loco_delete_select",
            data_schema=self._loco_select_schema(),
        )

    # --- Done --------------------------------------------------------------

    async def async_step_done(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Persist both working lists and finish.

        If the meaningful turnout *and* loco content (name + address + flags, in
        order) is unchanged, re-emit the stored options verbatim so Home
        Assistant sees no diff and :class:`OptionsFlowWithReload` skips the reload
        — a look-only session (or one that only backfilled internal ids) must not
        tear down the live Z21 connection.
        """
        stored = self.config_entry.options
        turnouts_changed = self._turnout_content(
            self._turnout_working
        ) != self._turnout_content(stored.get(CONF_TURNOUTS, []))
        locos_changed = self._loco_content(
            self._loco_working
        ) != self._loco_content(stored.get(CONF_LOCOS, []))

        if not turnouts_changed and not locos_changed:
            return self.async_create_entry(data=dict(stored))

        self._migrate_edited_turnouts()
        self._migrate_edited_locos()
        options = dict(stored)
        options[CONF_TURNOUTS] = self._turnout_working
        options[CONF_LOCOS] = self._loco_working
        return self.async_create_entry(data=options)

    @staticmethod
    def _turnout_content(turnouts: list[dict]) -> list[tuple[str, int, bool]]:
        """The user-meaningful shape of a turnout list, ignoring internal ids."""
        return [
            (
                t[CONF_TURNOUT_NAME],
                int(t[CONF_TURNOUT_FADR]),
                bool(t.get(CONF_TURNOUT_INVERTED, False)),
            )
            for t in turnouts
        ]

    @staticmethod
    def _loco_content(locos: list[dict]) -> list[tuple[str, int, int]]:
        """The user-meaningful shape of a loco list, ignoring internal ids."""
        return [
            (
                l[CONF_LOCO_NAME],
                int(l[CONF_LOCO_ADDRESS]),
                int(l[CONF_LOCO_SPEED_STEPS]),
            )
            for l in locos
        ]

    # --- Helpers -----------------------------------------------------------

    @staticmethod
    def _find(items: list[dict], item_id: str | None) -> dict | None:
        """Return the item in ``items`` whose ``id`` matches, or None."""
        return next((i for i in items if i["id"] == item_id), None)

    def _validate_turnout_unique(
        self, fadr: int | float, *, exclude_id: str | None = None
    ) -> str | None:
        """Return an error key if ``fadr`` collides with another turnout."""
        fadr = int(fadr)
        for t in self._turnout_working:
            if t[CONF_TURNOUT_ID] == exclude_id:
                continue
            if t[CONF_TURNOUT_FADR] == fadr:
                return "duplicate_address"
        return None

    def _validate_loco_unique(
        self, address: int | float, *, exclude_id: str | None = None
    ) -> str | None:
        """Return an error key if ``address`` collides with another loco."""
        address = int(address)
        for l in self._loco_working:
            if l[CONF_LOCO_ID] == exclude_id:
                continue
            if l[CONF_LOCO_ADDRESS] == address:
                return "duplicate_address"
        return None

    def _validate_loco_add(self, address: int | float) -> str | None:
        """Validate a loco add: enforce the 16-loco cap, then uniqueness.

        The cap is checked first so a full roster is rejected outright with
        ``too_many_locos`` rather than masking it behind an address collision.
        """
        if len(self._loco_working) >= LOCO_MAX:
            return "too_many_locos"
        return self._validate_loco_unique(address)

    def _turnout_select_schema(self) -> vol.Schema:
        """A one-field schema: a dropdown of turnouts labelled by name."""
        options = [
            {
                "value": t[CONF_TURNOUT_ID],
                "label": f"{t[CONF_TURNOUT_NAME]} (FAdr {t[CONF_TURNOUT_FADR]})",
            }
            for t in self._turnout_working
        ]
        return vol.Schema({
            vol.Required(CONF_TURNOUT_ID): SelectSelector(
                SelectSelectorConfig(
                    options=options, mode=SelectSelectorMode.DROPDOWN
                )
            )
        })

    def _loco_select_schema(self) -> vol.Schema:
        """A one-field schema: a dropdown of locos labelled by name."""
        options = [
            {
                "value": l[CONF_LOCO_ID],
                "label": f"{l[CONF_LOCO_NAME]} (address {l[CONF_LOCO_ADDRESS]})",
            }
            for l in self._loco_working
        ]
        return vol.Schema({
            vol.Required(CONF_LOCO_ID): SelectSelector(
                SelectSelectorConfig(
                    options=options, mode=SelectSelectorMode.DROPDOWN
                )
            )
        })

    def _migrate_edited_turnouts(self) -> None:
        """Carry each turnout's switch entity across an FAdr change.

        The switch unique_id is ``{serial}_turnout_{fadr}``; when a turnout keeps
        its stable id but changes FAdr, rename the existing registry entry so its
        history/area/customisations survive instead of orphaning as unavailable.
        """
        original = {
            t[CONF_TURNOUT_ID]: t
            for t in self.config_entry.options.get(CONF_TURNOUTS, [])
            if CONF_TURNOUT_ID in t
        }
        serial = self.config_entry.data[CONF_SERIAL]

        moves: list[tuple[str, str, str]] = []
        for t in self._turnout_working:
            old = original.get(t[CONF_TURNOUT_ID])
            if old is None or old[CONF_TURNOUT_FADR] == t[CONF_TURNOUT_FADR]:
                continue
            moves.append((
                "switch",
                f"{serial}_turnout_{old[CONF_TURNOUT_FADR]}",
                f"{serial}_turnout_{t[CONF_TURNOUT_FADR]}",
            ))
        self._apply_migrations(moves)

    def _migrate_edited_locos(self) -> None:
        """Carry each loco's entities across a DCC-address change.

        A loco owns three entities keyed by ``{serial}_loco_{address}_{suffix}``
        (``number`` speed, ``switch`` direction, ``button`` e-stop). When a loco
        keeps its stable id but changes address, rename each existing registry
        entry so history/area/customisations survive instead of orphaning as
        unavailable.
        """
        original = {
            l[CONF_LOCO_ID]: l
            for l in self.config_entry.options.get(CONF_LOCOS, [])
            if CONF_LOCO_ID in l
        }
        serial = self.config_entry.data[CONF_SERIAL]
        # (platform, unique_id suffix) for each per-loco entity.
        entities = (
            ("number", "speed"),
            ("switch", "direction"),
            ("button", "estop"),
        )

        moves: list[tuple[str, str, str]] = []
        for l in self._loco_working:
            old = original.get(l[CONF_LOCO_ID])
            if old is None or old[CONF_LOCO_ADDRESS] == l[CONF_LOCO_ADDRESS]:
                continue
            for platform, suffix in entities:
                moves.append((
                    platform,
                    f"{serial}_loco_{old[CONF_LOCO_ADDRESS]}_{suffix}",
                    f"{serial}_loco_{l[CONF_LOCO_ADDRESS]}_{suffix}",
                ))
        self._apply_migrations(moves)

    def _apply_migrations(self, moves: list[tuple[str, str, str]]) -> None:
        """Rename registry entries in **two phases** so a swap can't collide.

        Each ``(platform, old_unique_id, new_unique_id)`` mover is first parked on
        a temporary unique_id, then settled on its target. A one-phase rename in
        list order would raise ``ValueError`` if a target unique_id is still held
        by another entity that is itself scheduled to move later in the batch.
        """
        registry = er.async_get(self.hass)

        # Resolve to concrete entity_ids, skipping entities that don't exist.
        resolved: list[tuple[str, str]] = []
        for platform, old_uid, new_uid in moves:
            entity_id = registry.async_get_entity_id(platform, DOMAIN, old_uid)
            if entity_id is not None:
                resolved.append((entity_id, new_uid))

        # Phase 1: park each mover on a collision-proof temporary unique_id.
        for entity_id, _target in resolved:
            registry.async_update_entity(
                entity_id, new_unique_id=f"migrating_{entity_id}"
            )
        # Phase 2: settle each on its target, now guaranteed free.
        for entity_id, target in resolved:
            registry.async_update_entity(entity_id, new_unique_id=target)
