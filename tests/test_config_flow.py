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
    DOMAIN,
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
