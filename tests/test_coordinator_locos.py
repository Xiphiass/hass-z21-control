"""Coordinator loco subscription and last-known drive state (issue #48, ADR-0003).

The coordinator subscribes every configured loco (LAN_X_GET_LOCO_INFO) on setup
and on recovery-from-silence, stores each inbound LocoInfo as the last-known
per-address state, and composes every drive command from it because speed and
direction are one coupled wire command.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.z21.coordinator import Z21Coordinator
from custom_components.z21.protocol import (
    HDR_LOCO_INFO,
    HDR_SYSTEMSTATE_DATACHANGED,
    LocoInfo,
    SystemState,
)


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.connect = AsyncMock()
    return client


def _make_coordinator(mock_client, locos=None, turnouts=None):
    """Build a coordinator whose entry exposes the given locos/turnouts."""
    entry = MagicMock()
    entry.options = {"locos": locos or [], "turnouts": turnouts or []}
    coordinator = Z21Coordinator(hass=MagicMock(), entry=entry, client=mock_client)
    # DataUpdateCoordinator.__init__ resets config_entry from a contextvar (None
    # in unit tests), so re-attach the entry the coordinator should read.
    coordinator.config_entry = entry
    return coordinator


def _loco(address, speed_steps=128):
    return {"id": f"id{address}", "name": f"L{address}", "address": address,
            "speed_steps": speed_steps}


def _info(address, *, forward=True, speed=0, estop=False, speed_steps=128):
    return LocoInfo(address=address, forward=forward, speed=speed, estop=estop,
                    speed_steps=speed_steps, busy=False)


def _system_state():
    return SystemState(
        main_current=0, prog_current=0, filtered_main_current=0, temperature=20,
        supply_voltage=12000, vcc_voltage=12000, central_state=0,
        central_state_ex=0, capabilities=0, emergency_stop=False,
        track_voltage_off=False, short_circuit=False,
        programming_mode_active=False, high_temperature=False, power_lost=False,
        capabilities_valid=False,
    )


def _requested(mock_client):
    return [c.args[0] for c in mock_client.request_loco_info.call_args_list]


# --- Discovery ---------------------------------------------------------------


def test_setup_subscribes_every_configured_loco(mock_client):
    coordinator = _make_coordinator(
        mock_client, locos=[_loco(3), _loco(300)], turnouts=[{"fadr": 4}]
    )
    asyncio.run(coordinator.async_setup())

    assert _requested(mock_client) == [3, 300]
    # Turnout discovery still runs alongside.
    assert [c.args[0] for c in mock_client.request_turnout_info.call_args_list] == [4]


def test_setup_without_locos_sends_no_subscription(mock_client):
    coordinator = _make_coordinator(mock_client)
    asyncio.run(coordinator.async_setup())

    mock_client.request_loco_info.assert_not_called()


def test_stale_recovery_resubscribes_locos(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3), _loco(7)])
    coordinator._last_rx = 0.0
    coordinator._stale = True

    coordinator._handle_message(HDR_SYSTEMSTATE_DATACHANGED, _system_state())

    assert _requested(mock_client) == [3, 7]


def test_no_resubscribe_without_stale(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    coordinator._last_rx = 0.0

    coordinator._handle_message(HDR_SYSTEMSTATE_DATACHANGED, _system_state())

    mock_client.request_loco_info.assert_not_called()


# --- Last-known state ----------------------------------------------------------


def test_loco_info_updates_state_and_notifies_listeners(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    notified = []
    coordinator.async_add_listener(lambda: notified.append(True))

    info = _info(3, forward=False, speed=20)
    coordinator._handle_message(HDR_LOCO_INFO, info)

    assert coordinator.loco_states == {3: info}
    assert notified == [True]


def test_loco_info_replaces_previous_state(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    coordinator._handle_message(HDR_LOCO_INFO, _info(3, speed=20))
    coordinator._handle_message(HDR_LOCO_INFO, _info(3, speed=5, forward=False))

    assert coordinator.loco_states[3].speed == 5
    assert coordinator.loco_states[3].forward is False


def test_loco_states_empty_before_feedback_and_returns_copy(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    assert coordinator.loco_states == {}

    coordinator._handle_message(HDR_LOCO_INFO, _info(3))
    states = coordinator.loco_states
    states.clear()
    assert 3 in coordinator.loco_states


def test_non_loco_payload_under_loco_header_ignored(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    coordinator._handle_message(HDR_LOCO_INFO, "garbage")
    assert coordinator.loco_states == {}


# --- drive_loco ------------------------------------------------------------------


def _drive_kwargs(mock_client):
    mock_client.set_loco_drive.assert_called_once()
    call = mock_client.set_loco_drive.call_args
    return call.args, call.kwargs


def test_drive_loco_defaults_forward_speed_zero_without_feedback(mock_client):
    """No feedback yet: speed-only defaults to forward, direction-only to speed 0."""
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])

    coordinator.drive_loco(3, speed=10)
    args, kwargs = _drive_kwargs(mock_client)
    assert args == (3,)
    assert kwargs == {"step": 10, "forward": True, "speed_steps": 128,
                      "estop": False}

    mock_client.set_loco_drive.reset_mock()
    coordinator.drive_loco(3, forward=False)
    _, kwargs = _drive_kwargs(mock_client)
    assert (kwargs["step"], kwargs["forward"]) == (0, False)


def test_drive_loco_speed_preserves_last_known_direction(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    coordinator._handle_message(HDR_LOCO_INFO, _info(3, forward=False, speed=20))

    coordinator.drive_loco(3, speed=40)

    _, kwargs = _drive_kwargs(mock_client)
    assert (kwargs["step"], kwargs["forward"]) == (40, False)


def test_drive_loco_direction_preserves_last_known_speed(mock_client):
    """A direction flip while moving keeps the current speed (no implicit stop)."""
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    coordinator._handle_message(HDR_LOCO_INFO, _info(3, forward=True, speed=20))

    coordinator.drive_loco(3, forward=False)

    _, kwargs = _drive_kwargs(mock_client)
    assert (kwargs["step"], kwargs["forward"]) == (20, False)


def test_drive_loco_estop_preserves_direction(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    coordinator._handle_message(HDR_LOCO_INFO, _info(3, forward=False, speed=20))

    coordinator.drive_loco(3, estop=True)

    _, kwargs = _drive_kwargs(mock_client)
    assert kwargs["forward"] is False
    assert kwargs["estop"] is True


def test_drive_loco_uses_configured_speed_steps(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3, speed_steps=28)])

    coordinator.drive_loco(3, speed=5)

    _, kwargs = _drive_kwargs(mock_client)
    assert kwargs["speed_steps"] == 28


def test_drive_loco_does_not_update_state_optimistically(mock_client):
    """State follows the Z21's feedback, not the command (non-optimistic)."""
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    coordinator._handle_message(HDR_LOCO_INFO, _info(3, speed=20))

    coordinator.drive_loco(3, speed=40)

    assert coordinator.loco_states[3].speed == 20


def test_drive_loco_always_sends_even_when_unchanged(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3)])
    coordinator._handle_message(HDR_LOCO_INFO, _info(3, speed=20))

    coordinator.drive_loco(3, speed=20)

    mock_client.set_loco_drive.assert_called_once()


# --- drive_loco: reported vs configured step-mode mismatch (ADR-0003) --------


def test_drive_loco_direction_rescales_wider_reported_mode(mock_client):
    """128-reported step 100 on a 28-configured loco flips at ~100/126, not 3/28."""
    coordinator = _make_coordinator(mock_client, locos=[_loco(3, speed_steps=28)])
    coordinator._handle_message(
        HDR_LOCO_INFO, _info(3, forward=True, speed=100, speed_steps=128)
    )

    coordinator.drive_loco(3, forward=False)

    _, kwargs = _drive_kwargs(mock_client)
    assert kwargs == {"step": 22, "forward": False, "speed_steps": 28,
                      "estop": False}


def test_drive_loco_direction_rescales_narrower_reported_mode(mock_client):
    """28-reported step 20 on a 128-configured loco flips at 90/126, not 20/126."""
    coordinator = _make_coordinator(mock_client, locos=[_loco(3, speed_steps=128)])
    coordinator._handle_message(
        HDR_LOCO_INFO, _info(3, forward=True, speed=20, speed_steps=28)
    )

    coordinator.drive_loco(3, forward=False)

    _, kwargs = _drive_kwargs(mock_client)
    assert (kwargs["step"], kwargs["speed_steps"]) == (90, 128)


def test_drive_loco_estop_rescales_last_known_speed(mock_client):
    coordinator = _make_coordinator(mock_client, locos=[_loco(3, speed_steps=28)])
    coordinator._handle_message(
        HDR_LOCO_INFO, _info(3, forward=False, speed=100, speed_steps=128)
    )

    coordinator.drive_loco(3, estop=True)

    _, kwargs = _drive_kwargs(mock_client)
    assert (kwargs["step"], kwargs["forward"], kwargs["estop"]) == (22, False, True)


def test_drive_loco_rescale_keeps_a_moving_loco_moving(mock_client):
    """A crawl in a finer mode never rounds down to Stop in a coarser one."""
    coordinator = _make_coordinator(mock_client, locos=[_loco(3, speed_steps=14)])
    coordinator._handle_message(
        HDR_LOCO_INFO, _info(3, speed=1, speed_steps=128)
    )

    coordinator.drive_loco(3, forward=False)

    _, kwargs = _drive_kwargs(mock_client)
    assert kwargs["step"] == 1


def test_drive_loco_explicit_speed_is_not_rescaled(mock_client):
    """An explicit speed is already in the configured mode (the slider's)."""
    coordinator = _make_coordinator(mock_client, locos=[_loco(3, speed_steps=28)])
    coordinator._handle_message(
        HDR_LOCO_INFO, _info(3, speed=100, speed_steps=128)
    )

    coordinator.drive_loco(3, speed=10)

    _, kwargs = _drive_kwargs(mock_client)
    assert kwargs["step"] == 10
