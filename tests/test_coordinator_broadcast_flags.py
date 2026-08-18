"""Coordinator broadcast flag and turnout position tests (issue #29).

The coordinator must subscribe to BOTH system state AND driving & switching
broadcast flags, and must store turnout positions from LAN_X_TURNOUT_INFO
messages.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.z21.coordinator import Z21Coordinator
from custom_components.z21.protocol import (
    BROADCAST_FLAG_DRIVING_SWITCHING,
    BROADCAST_FLAG_SYSTEM_STATE,
    HDR_TURNOUT_INFO,
    TurnoutInfo,
)


@pytest.fixture
def mock_client():
    """Return a mock Z21Client with a set_broadcastflags method."""
    client = MagicMock()
    client.set_broadcastflags.return_value = None
    client.connect = AsyncMock()
    return client


def test_coordinator_subscribes_to_combined_broadcast_flags(mock_client):
    """The coordinator should subscribe to BOTH system state AND driving & switching flags."""
    combined_flags = (
        BROADCAST_FLAG_SYSTEM_STATE | BROADCAST_FLAG_DRIVING_SWITCHING
    )

    with patch(
        "custom_components.z21.coordinator.Z21Client", return_value=mock_client
    ), patch(
        "custom_components.z21.coordinator.HomeAssistant"
    ), patch(
        "custom_components.z21.coordinator.ConfigEntry"
    ):
        coordinator = Z21Coordinator(
            hass=MagicMock(),
            entry=MagicMock(),
            client=mock_client,
        )

        # Simulate the async_setup flow
        import asyncio

        asyncio.get_event_loop().run_until_complete(coordinator.async_setup())

        # Verify set_broadcastflags was called with the combined flags
        mock_client.set_broadcastflags.assert_called_once_with(
            combined_flags
        )


def test_coordinator_stores_turnout_position(mock_client):
    """When a LAN_X_TURNOUT_INFO arrives, the coordinator stores the position."""
    with patch(
        "custom_components.z21.coordinator.Z21Client", return_value=mock_client
    ), patch(
        "custom_components.z21.coordinator.HomeAssistant"
    ), patch(
        "custom_components.z21.coordinator.ConfigEntry"
    ):
        coordinator = Z21Coordinator(
            hass=MagicMock(),
            entry=MagicMock(),
            client=mock_client,
        )
        coordinator._last_rx = 0.0  # Prevent stale re-send on first message

        # Simulate a turnout info broadcast
        turnout = TurnoutInfo(fadr=4, position=1, invalid=False)
        coordinator._handle_message(HDR_TURNOUT_INFO, turnout)

        assert coordinator._turnout_positions == {4: 1}


def test_coordinator_stores_turnout_position_closed(mock_client):
    """A turnout position of 0 (closed/straight) is stored correctly."""
    with patch(
        "custom_components.z21.coordinator.Z21Client", return_value=mock_client
    ), patch(
        "custom_components.z21.coordinator.HomeAssistant"
    ), patch(
        "custom_components.z21.coordinator.ConfigEntry"
    ):
        coordinator = Z21Coordinator(
            hass=MagicMock(),
            entry=MagicMock(),
            client=mock_client,
        )
        coordinator._last_rx = 0.0

        # Simulate a turnout info broadcast with position 0 (closed)
        turnout = TurnoutInfo(fadr=7, position=0, invalid=False)
        coordinator._handle_message(HDR_TURNOUT_INFO, turnout)

        assert coordinator._turnout_positions == {7: 0}


def test_coordinator_updates_turnout_position(mock_client):
    """Subsequent turnout info messages update the position."""
    with patch(
        "custom_components.z21.coordinator.Z21Client", return_value=mock_client
    ), patch(
        "custom_components.z21.coordinator.HomeAssistant"
    ), patch(
        "custom_components.z21.coordinator.ConfigEntry"
    ):
        coordinator = Z21Coordinator(
            hass=MagicMock(),
            entry=MagicMock(),
            client=mock_client,
        )
        coordinator._last_rx = 0.0

        # First: closed
        turnout1 = TurnoutInfo(fadr=4, position=0, invalid=False)
        coordinator._handle_message(HDR_TURNOUT_INFO, turnout1)
        assert coordinator._turnout_positions == {4: 0}

        # Then: diverged
        turnout2 = TurnoutInfo(fadr=4, position=1, invalid=False)
        coordinator._handle_message(HDR_TURNOUT_INFO, turnout2)
        assert coordinator._turnout_positions == {4: 1}


def test_turnout_positions_property_returns_copy(mock_client):
    """turnout_positions returns a copy, not the internal dict."""
    with patch(
        "custom_components.z21.coordinator.Z21Client", return_value=mock_client
    ), patch(
        "custom_components.z21.coordinator.HomeAssistant"
    ), patch(
        "custom_components.z21.coordinator.ConfigEntry"
    ):
        coordinator = Z21Coordinator(
            hass=MagicMock(),
            entry=MagicMock(),
            client=mock_client,
        )
        coordinator._last_rx = 0.0

        # Store a position
        turnout = TurnoutInfo(fadr=5, position=1, invalid=False)
        coordinator._handle_message(HDR_TURNOUT_INFO, turnout)

        # Get the property
        positions = coordinator.turnout_positions

        # Should be a copy
        assert positions == {5: 1}
        assert positions is not coordinator._turnout_positions

        # Modifying the copy doesn't affect the internal dict
        positions[5] = 0
        assert coordinator._turnout_positions == {5: 1}


def test_turnout_positions_empty_when_no_messages(mock_client):
    """turnout_positions returns an empty dict before any turnout info arrives."""
    with patch(
        "custom_components.z21.coordinator.Z21Client", return_value=mock_client
    ), patch(
        "custom_components.z21.coordinator.HomeAssistant"
    ), patch(
        "custom_components.z21.coordinator.ConfigEntry"
    ):
        coordinator = Z21Coordinator(
            hass=MagicMock(),
            entry=MagicMock(),
            client=mock_client,
        )

        positions = coordinator.turnout_positions
        assert positions == {}
        assert isinstance(positions, dict)


def test_coordinator_ignores_non_turnout_info(mock_client):
    """Non-turnout-info messages don't affect _turnout_positions."""
    with patch(
        "custom_components.z21.coordinator.Z21Client", return_value=mock_client
    ), patch(
        "custom_components.z21.coordinator.HomeAssistant"
    ), patch(
        "custom_components.z21.coordinator.ConfigEntry"
    ):
        coordinator = Z21Coordinator(
            hass=MagicMock(),
            entry=MagicMock(),
            client=mock_client,
        )
        coordinator._last_rx = 0.0

        # Store a position first
        turnout = TurnoutInfo(fadr=4, position=1, invalid=False)
        coordinator._handle_message(HDR_TURNOUT_INFO, turnout)
        assert coordinator._turnout_positions == {4: 1}

        # Now send a non-turnout message (e.g., garbage)
        coordinator._handle_message(0xFFFF, "garbage")

        # Position should be unchanged
        assert coordinator._turnout_positions == {4: 1}


def test_coordinator_stale_recovery_sends_combined_flags(mock_client):
    """When stale recovers, the coordinator re-sends combined broadcast flags."""
    with patch(
        "custom_components.z21.coordinator.Z21Client", return_value=mock_client
    ), patch(
        "custom_components.z21.coordinator.HomeAssistant"
    ), patch(
        "custom_components.z21.coordinator.ConfigEntry"
    ):
        coordinator = Z21Coordinator(
            hass=MagicMock(),
            entry=MagicMock(),
            client=mock_client,
        )
        coordinator._last_rx = 0.0
        coordinator._stale = True  # Simulate stale state

        combined_flags = (
            BROADCAST_FLAG_SYSTEM_STATE | BROADCAST_FLAG_DRIVING_SWITCHING
        )

        # Simulate a system state message arriving (recovery)
        from custom_components.z21.protocol import (
            HDR_SYSTEMSTATE_DATACHANGED,
            SystemState,
        )

        system_state = SystemState(
            main_current=0,
            prog_current=0,
            filtered_main_current=0,
            temperature=20,
            supply_voltage=12000,
            vcc_voltage=12000,
            central_state=0,
            central_state_ex=0,
            capabilities=0,
            emergency_stop=False,
            track_voltage_off=False,
            short_circuit=False,
            programming_mode_active=False,
            high_temperature=False,
            power_lost=False,
            capabilities_valid=False,
        )

        coordinator._handle_message(HDR_SYSTEMSTATE_DATACHANGED, system_state)

        # Verify combined flags were sent during stale recovery
        assert mock_client.set_broadcastflags.call_count == 1
        mock_client.set_broadcastflags.assert_called_with(combined_flags)