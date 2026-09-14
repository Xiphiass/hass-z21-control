"""Config-flow tests for the Z21 integration (seam 2, faked transport).

Covers the three acceptance paths from issue #4 — success, fail-fast on an
unreachable IP, and duplicate-serial abort — by injecting a fake UDP transport
into the client the flow constructs. No physical Z21, no real socket. These
tests are HA-coupled and run via pytest-homeassistant-custom-component
(``asyncio_mode = auto``), which is a deliberate exception to the HA-free
``asyncio.run`` style of the protocol/client suites.
"""

from __future__ import annotations

import struct
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.z21 import protocol
from custom_components.z21.client import Z21Client
from custom_components.z21.const import (
    CONF_FW_VERSION,
    CONF_HW_TYPE,
    CONF_SERIAL,
    CONF_TURNOUT_FADR,
    CONF_TURNOUT_ID,
    CONF_TURNOUT_NAME,
    CONF_TURNOUTS,
    DOMAIN,
    TURNOUT_FADR_MAX,
    TURNOUT_FADR_MIN,
    format_fw_version,
    hw_type_name,
)

_HOST = "192.0.2.10"
_SERIAL = 0xABCD
_HW_TYPE = 0x00000201
_FW_VERSION = 0x0143


def _serial_response(serial: int) -> bytes:
    return protocol.build_frame(protocol.HDR_SERIAL_NUMBER, struct.pack("<I", serial))


def _hwinfo_response(hw: int, fw: int) -> bytes:
    return protocol.build_frame(protocol.HDR_HWINFO, struct.pack("<II", hw, fw))


def _system_state_response() -> bytes:
    electrical = struct.pack("<hhhhHH", 0, 0, 0, 20, 15000, 15000)
    return protocol.build_frame(
        protocol.HDR_SYSTEMSTATE_DATACHANGED, electrical + bytes(4)
    )


def _install_client(monkeypatch, *, responder) -> None:
    """Patch the ``Z21Client`` used by the flow *and* entry setup with a fake.

    A successful flow triggers ``async_setup_entry``, which opens its own live
    client, so both module references are patched. ``responder(header, client)``
    is called after each send (as by the real Z21) and may feed scripted
    datagrams via ``client._on_datagram``. A ``None`` responder simulates a Z21
    that never answers -> ``Z21Timeout``.
    """

    class _FakeClient(Z21Client):
        async def open(self) -> None:
            if self._transport is not None:
                return
            self._attach_transport(_FakeTransport(self, responder))

    monkeypatch.setattr(
        "custom_components.z21.config_flow.Z21Client", _FakeClient
    )
    monkeypatch.setattr("custom_components.z21.Z21Client", _FakeClient)
    monkeypatch.setattr("custom_components.z21.coordinator._STATE_TIMEOUT", 0.2)
    # Keep the flow's validation budget tiny so the fail-fast test is quick.
    monkeypatch.setattr("custom_components.z21.config_flow._CONNECT_TIMEOUT", 0.05)
    monkeypatch.setattr("custom_components.z21.config_flow._CONNECT_RETRIES", 1)
    monkeypatch.setattr("custom_components.z21.config_flow._CONNECT_BACKOFF", 0.0)


class _FakeTransport:
    """Records sends; invokes ``responder`` to script Z21 replies."""

    def __init__(self, client: Z21Client, responder) -> None:
        self.sent: list[bytes] = []
        self.closed = False
        self._client = client
        self._responder = responder

    def sendto(self, data: bytes, addr: object = None) -> None:
        self.sent.append(data)
        if self._responder is not None:
            header = int.from_bytes(data[2:4], "little")
            self._responder(header, self._client)

    def close(self) -> None:
        self.closed = True


def _answering_responder(serial: int, hw: int, fw: int):
    def responder(header, client):
        if header == protocol.HDR_SERIAL_NUMBER:
            client._on_datagram(_serial_response(serial))
        elif header == protocol.HDR_HWINFO:
            client._on_datagram(_hwinfo_response(hw, fw))
        elif header == protocol.HDR_SYSTEMSTATE_GETDATA:
            # The created entry's coordinator polls System State on setup.
            client._on_datagram(_system_state_response())

    return responder


async def test_user_flow_success(hass: HomeAssistant, monkeypatch) -> None:
    """A valid, reachable IP creates an entry and registers the device."""
    _install_client(
        monkeypatch,
        responder=_answering_responder(_SERIAL, _HW_TYPE, _FW_VERSION),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: _HOST}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]
    assert entry.unique_id == str(_SERIAL)
    assert entry.data == {
        CONF_HOST: _HOST,
        CONF_SERIAL: _SERIAL,
        CONF_HW_TYPE: _HW_TYPE,
        CONF_FW_VERSION: _FW_VERSION,
    }

    device = dr.async_get(hass).async_get_device(
        identifiers={(DOMAIN, str(_SERIAL))}
    )
    assert device is not None
    assert device.model == hw_type_name(_HW_TYPE)
    assert device.sw_version == format_fw_version(_FW_VERSION)


async def test_user_flow_cannot_connect(hass: HomeAssistant, monkeypatch) -> None:
    """An unreachable IP fails fast with cannot_connect and creates no entry."""
    _install_client(monkeypatch, responder=None)  # never answers -> Z21Timeout

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: _HOST}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert hass.config_entries.async_entries(DOMAIN) == []


async def test_user_flow_duplicate_aborts(hass: HomeAssistant, monkeypatch) -> None:
    """Adding the same Z21 (same serial) again is aborted as a duplicate."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=str(_SERIAL),
        data={
            CONF_HOST: "192.0.2.99",
            CONF_SERIAL: _SERIAL,
            CONF_HW_TYPE: _HW_TYPE,
            CONF_FW_VERSION: _FW_VERSION,
        },
    ).add_to_hass(hass)

    _install_client(
        monkeypatch,
        responder=_answering_responder(_SERIAL, _HW_TYPE, _FW_VERSION),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: _HOST}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


def _entry(turnouts: list[dict] | None = None) -> MockConfigEntry:
    """A configured Z21 entry, optionally seeded with turnouts."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=str(_SERIAL),
        data={
            CONF_HOST: _HOST,
            CONF_SERIAL: _SERIAL,
            CONF_HW_TYPE: _HW_TYPE,
            CONF_FW_VERSION: _FW_VERSION,
        },
        options={CONF_TURNOUTS: turnouts} if turnouts is not None else {},
    )


async def _open_menu(hass: HomeAssistant, entry: MockConfigEntry):
    """Init the options flow and return the menu result."""
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"
    return result


async def _pick(hass: HomeAssistant, flow_id: str, step: str):
    """Choose a menu option by its next step id."""
    return await hass.config_entries.options.async_configure(
        flow_id, {"next_step_id": step}
    )


async def _finish(hass: HomeAssistant, flow_id: str):
    """Choose Done, suppressing the real reload OptionsFlowWithReload schedules.

    The entry is only ``add_to_hass``'d (never set up) in these tests, so an
    actual reload would try to open a real socket. We only care that the options
    were persisted; the reload itself is exercised in
    ``test_options_flow_done_reloads_entry``.
    """
    with patch.object(hass.config_entries, "async_schedule_reload"):
        return await _pick(hass, flow_id, "done")


async def test_options_flow_menu_hides_edit_delete_when_empty(
    hass: HomeAssistant,
) -> None:
    """With no turnouts, the menu offers only add and done."""
    entry = _entry()
    entry.add_to_hass(hass)

    result = await _open_menu(hass, entry)
    assert set(result["menu_options"]) == {"add", "done"}


async def test_options_flow_menu_shows_edit_delete_when_present(
    hass: HomeAssistant,
) -> None:
    """With turnouts, the menu offers edit and delete too."""
    entry = _entry([{CONF_TURNOUT_NAME: "A", CONF_TURNOUT_FADR: 4}])
    entry.add_to_hass(hass)

    result = await _open_menu(hass, entry)
    assert set(result["menu_options"]) == {"add", "edit_select", "delete_select", "done"}


async def test_options_flow_add_then_done(hass: HomeAssistant) -> None:
    """Add a turnout, then Done persists it (with a stable id)."""
    entry = _entry()
    entry.add_to_hass(hass)

    result = await _open_menu(hass, entry)
    result = await _pick(hass, result["flow_id"], "add")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add"

    # Submit the add form -> back to the menu.
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_TURNOUT_NAME: "Turnout 1", CONF_TURNOUT_FADR: 100},
    )
    assert result["type"] is FlowResultType.MENU

    # Done -> persist.
    result = await _finish(hass, result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY
    turnouts = result["data"][CONF_TURNOUTS]
    assert len(turnouts) == 1
    assert turnouts[0][CONF_TURNOUT_NAME] == "Turnout 1"
    assert turnouts[0][CONF_TURNOUT_FADR] == 100
    assert turnouts[0][CONF_TURNOUT_ID]  # stable id assigned


async def test_options_flow_duplicate_fadr_rejected(hass: HomeAssistant) -> None:
    """Adding a turnout with a duplicate FAdr shows the duplicate_address error."""
    entry = _entry([{CONF_TURNOUT_NAME: "Turnout 1", CONF_TURNOUT_FADR: 100}])
    entry.add_to_hass(hass)

    result = await _open_menu(hass, entry)
    result = await _pick(hass, result["flow_id"], "add")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_TURNOUT_NAME: "Turnout 2", CONF_TURNOUT_FADR: 100},  # duplicate
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "duplicate_address"}


async def test_options_flow_edit_turnout(hass: HomeAssistant) -> None:
    """Editing a turnout updates its name and address."""
    entry = _entry([{CONF_TURNOUT_NAME: "Old", CONF_TURNOUT_FADR: 100}])
    entry.add_to_hass(hass)

    result = await _open_menu(hass, entry)
    result = await _pick(hass, result["flow_id"], "edit_select")
    assert result["step_id"] == "edit_select"

    # Pick the (only) turnout by its stable id. The seeded turnout had no id;
    # the flow backfills one, so read the value offered by the select schema.
    options = result["data_schema"].schema[CONF_TURNOUT_ID].config["options"]
    turnout_id = options[0]["value"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_TURNOUT_ID: turnout_id}
    )
    assert result["step_id"] == "edit"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_TURNOUT_NAME: "New", CONF_TURNOUT_FADR: 200},
    )
    assert result["type"] is FlowResultType.MENU

    result = await _finish(hass, result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY
    turnouts = result["data"][CONF_TURNOUTS]
    assert len(turnouts) == 1
    assert turnouts[0][CONF_TURNOUT_NAME] == "New"
    assert turnouts[0][CONF_TURNOUT_FADR] == 200


async def test_options_flow_delete_turnout(hass: HomeAssistant) -> None:
    """Deleting a turnout removes it from the list."""
    entry = _entry(
        [
            {CONF_TURNOUT_NAME: "Turnout 1", CONF_TURNOUT_FADR: 100},
            {CONF_TURNOUT_NAME: "Turnout 2", CONF_TURNOUT_FADR: 200},
        ]
    )
    entry.add_to_hass(hass)

    result = await _open_menu(hass, entry)
    result = await _pick(hass, result["flow_id"], "delete_select")
    assert result["step_id"] == "delete_select"

    # Delete the first turnout by its stable id.
    options = result["data_schema"].schema[CONF_TURNOUT_ID].config["options"]
    first_id = options[0]["value"]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_TURNOUT_ID: first_id}
    )
    assert result["type"] is FlowResultType.MENU

    result = await _finish(hass, result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY
    turnouts = result["data"][CONF_TURNOUTS]
    assert len(turnouts) == 1
    assert turnouts[0][CONF_TURNOUT_FADR] == 200


async def test_options_flow_edit_address_migrates_entity(
    hass: HomeAssistant,
) -> None:
    """Editing a turnout's FAdr renames its switch entity's unique_id."""
    from homeassistant.helpers import entity_registry as er

    entry = _entry(
        [{CONF_TURNOUT_NAME: "A", CONF_TURNOUT_FADR: 100, CONF_TURNOUT_ID: "abc"}]
    )
    entry.add_to_hass(hass)

    # Pre-register the switch entity at the old FAdr-based unique_id.
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "switch",
        DOMAIN,
        f"{_SERIAL}_turnout_100",
        config_entry=entry,
    )

    result = await _open_menu(hass, entry)
    result = await _pick(hass, result["flow_id"], "edit_select")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_TURNOUT_ID: "abc"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_TURNOUT_NAME: "A", CONF_TURNOUT_FADR: 200},
    )
    result = await _finish(hass, result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # The entity now carries the new FAdr-based unique_id; the old one is gone.
    assert (
        registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_200")
        is not None
    )
    assert (
        registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_100")
        is None
    )


async def test_options_flow_swap_addresses_migrates_both(
    hass: HomeAssistant,
) -> None:
    """Swapping two turnouts' addresses migrates both entities without collision."""
    from homeassistant.helpers import entity_registry as er

    entry = _entry(
        [
            {CONF_TURNOUT_NAME: "A", CONF_TURNOUT_FADR: 100, CONF_TURNOUT_ID: "a"},
            {CONF_TURNOUT_NAME: "B", CONF_TURNOUT_FADR: 200, CONF_TURNOUT_ID: "b"},
        ]
    )
    entry.add_to_hass(hass)

    registry = er.async_get(hass)
    registry.async_get_or_create(
        "switch", DOMAIN, f"{_SERIAL}_turnout_100", config_entry=entry
    )
    registry.async_get_or_create(
        "switch", DOMAIN, f"{_SERIAL}_turnout_200", config_entry=entry
    )

    # Move B off 200 first (200 -> 300), then A onto 200 (100 -> 200). Without a
    # collision-safe migration, A's rename to 200 would raise while B still holds
    # a stale 200 entity.
    result = await _open_menu(hass, entry)
    result = await _pick(hass, result["flow_id"], "edit_select")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_TURNOUT_ID: "b"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_TURNOUT_NAME: "B", CONF_TURNOUT_FADR: 300}
    )
    result = await _pick(hass, result["flow_id"], "edit_select")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_TURNOUT_ID: "a"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_TURNOUT_NAME: "A", CONF_TURNOUT_FADR: 200}
    )
    result = await _finish(hass, result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Both entities carried over to their new addresses.
    assert (
        registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_200")
        is not None
    )
    assert (
        registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_300")
        is not None
    )
    assert (
        registry.async_get_entity_id("switch", DOMAIN, f"{_SERIAL}_turnout_100")
        is None
    )


async def test_options_flow_done_without_changes_skips_reload(
    hass: HomeAssistant,
) -> None:
    """A look-only Done must not reload (would drop the live Z21 connection)."""
    entry = _entry([{CONF_TURNOUT_NAME: "A", CONF_TURNOUT_FADR: 4}])
    entry.add_to_hass(hass)

    result = await _open_menu(hass, entry)
    with patch.object(hass.config_entries, "async_schedule_reload") as mock_reload:
        result = await _pick(hass, result["flow_id"], "done")
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    mock_reload.assert_not_called()


async def test_options_flow_done_reloads_entry(hass: HomeAssistant) -> None:
    """Finishing the options flow reloads the integration (OptionsFlowWithReload)."""
    entry = _entry()
    entry.add_to_hass(hass)

    result = await _open_menu(hass, entry)
    result = await _pick(hass, result["flow_id"], "add")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_TURNOUT_NAME: "T", CONF_TURNOUT_FADR: 5},
    )

    with patch.object(
        hass.config_entries, "async_schedule_reload"
    ) as mock_reload:
        result = await _pick(hass, result["flow_id"], "done")
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    mock_reload.assert_called_once_with(entry.entry_id)