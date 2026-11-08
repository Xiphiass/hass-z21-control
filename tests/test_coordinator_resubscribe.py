"""Keepalive re-asserts the Z21's per-client subscriptions.

The Z21 keeps broadcast flags and the (max 16, FIFO) loco subscriptions per
client and drops them whenever it forgets the client: a reboot, a logoff, or the
spec 1.1 eviction after a minute without communication. A plain
``LAN_SYSTEMSTATE_GETDATA`` (2.19) is still answered afterwards, so a gap
shorter than the staleness window never trips the stale-recovery path and the
loco entities silently freeze on their last state. Separately, a single lost
``LAN_X_LOCO_INFO`` datagram (UDP, spec 4) leaves a stopped loco reported as
moving until the next change.

These tests drive the coordinator against a small behavioural fake of the Z21
that honours those rules and assert the user-visible symptom: the last-known
loco state matches the station after a keepalive.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from custom_components.z21 import protocol
from custom_components.z21.coordinator import Z21Coordinator
from custom_components.z21.protocol import (
    HDR_LOCO_INFO,
    HDR_SYSTEMSTATE_DATACHANGED,
    LocoInfo,
    SystemState,
)


class FakeZ21:
    """Fake Z21 client that models the station's per-client subscription state.

    Exposes the ``Z21Client`` surface the coordinator uses. Replies are
    delivered synchronously to the subscribed handler.
    """

    def __init__(self) -> None:
        self.handler = None
        self.flags = 0
        self.subscribed: set[int] = set()
        self.locos: dict[int, int] = {}  # address -> speed
        self.drop_next_loco_info = False

    # --- station-side behaviour ---------------------------------------------

    def forget_client(self) -> None:
        """Reboot / eviction: per-client flags and loco subscriptions are lost."""
        self.flags = 0
        self.subscribed.clear()

    def handset_drive(self, address: int, speed: int) -> None:
        """Another controller changes a loco; subscribed clients are told."""
        self.locos[address] = speed
        if (
            address in self.subscribed
            and self.flags & protocol.BROADCAST_FLAG_DRIVING_SWITCHING
        ):
            if self.drop_next_loco_info:
                self.drop_next_loco_info = False
                return
            self._push_loco(address)

    def _push_loco(self, address: int) -> None:
        self.handler(
            HDR_LOCO_INFO,
            LocoInfo(address=address, forward=True, speed=self.locos[address],
                     estop=False, speed_steps=128, busy=False),
        )

    # --- Z21Client surface ---------------------------------------------------

    async def connect(self):
        return None

    def subscribe(self, handler):
        self.handler = handler
        return lambda: None

    def set_broadcastflags(self, flags):
        self.flags = flags

    def request_loco_info(self, address):
        self.subscribed.add(address)
        self.locos.setdefault(address, 0)
        self._push_loco(address)
        fut = asyncio.get_running_loop().create_future()
        fut.set_result(None)
        return fut

    def request_turnout_info(self, fadr):
        pass

    def request_systemstate(self):
        # Answered regardless of subscriptions (spec 2.19).
        self.handler(HDR_SYSTEMSTATE_DATACHANGED, _system_state())


def _system_state() -> SystemState:
    return SystemState(
        main_current=0, prog_current=0, filtered_main_current=0, temperature=20,
        supply_voltage=12000, vcc_voltage=12000, central_state=0,
        central_state_ex=0, capabilities=0, emergency_stop=False,
        track_voltage_off=False, short_circuit=False,
        programming_mode_active=False, high_temperature=False, power_lost=False,
        capabilities_valid=False,
    )


def _make_coordinator(z21: FakeZ21, loop) -> Z21Coordinator:
    entry = MagicMock()
    entry.options = {
        "locos": [{"id": "a", "name": "Stainz", "address": 3, "speed_steps": 128}],
        "turnouts": [],
    }
    hass = MagicMock()
    hass.loop = loop
    coordinator = Z21Coordinator(hass=hass, entry=entry, client=z21)
    coordinator.config_entry = entry
    coordinator.async_set_updated_data = MagicMock()
    coordinator.async_update_listeners = MagicMock()
    return coordinator


def test_keepalive_restores_loco_feedback_after_z21_forgets_client():
    async def scenario():
        z21 = FakeZ21()
        coordinator = _make_coordinator(z21, asyncio.get_running_loop())
        await coordinator.async_setup()
        z21.handset_drive(3, 50)
        assert coordinator.loco_states[3].speed == 50

        # The Z21 forgets the client but keeps answering polls: no stale edge.
        z21.forget_client()
        await coordinator._async_update_data()

        z21.handset_drive(3, 0)
        await coordinator._async_update_data()
        return coordinator.loco_states[3].speed

    assert asyncio.run(scenario()) == 0


def test_keepalive_corrects_state_after_lost_loco_info():
    async def scenario():
        z21 = FakeZ21()
        coordinator = _make_coordinator(z21, asyncio.get_running_loop())
        await coordinator.async_setup()
        z21.handset_drive(3, 50)

        z21.drop_next_loco_info = True  # the "stopped" datagram is lost
        z21.handset_drive(3, 0)
        assert coordinator.loco_states[3].speed == 50

        await coordinator._async_update_data()
        return coordinator.loco_states[3].speed

    assert asyncio.run(scenario()) == 0


class SlowZ21(FakeZ21):
    """A Z21 that answers loco polls late and drops one sent while it is busy.

    Real hardware takes ~0.6 s per ``LAN_X_LOCO_INFO`` reply and silently
    ignored the second of two back-to-back ``LAN_X_GET_LOCO_INFO`` requests
    (only the first loco ever got its state after a restart).
    """

    REPLY_DELAY = 0.02

    def __init__(self) -> None:
        super().__init__()
        self.busy = False

    def request_loco_info(self, address):
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        if self.busy:
            return fut  # dropped: never answered
        self.busy = True
        self.subscribed.add(address)
        self.locos.setdefault(address, 0)

        def _reply() -> None:
            self.busy = False
            self._push_loco(address)
            fut.set_result(None)

        loop.call_later(self.REPLY_DELAY, _reply)
        return fut


def test_keepalive_polls_locos_one_at_a_time(monkeypatch):
    """Every configured loco gets its state, even from a Z21 that drops bursts."""
    monkeypatch.setattr("custom_components.z21.coordinator.POLL_REPLY_TIMEOUT", 0.2)

    async def scenario():
        z21 = SlowZ21()
        coordinator = _make_coordinator(z21, asyncio.get_running_loop())
        coordinator.config_entry.options["locos"] = [
            {"id": "a", "name": "Stainz", "address": 11, "speed_steps": 128},
            {"id": "b", "name": "BR 203", "address": 12, "speed_steps": 128},
        ]
        z21.locos[12] = 40  # BR 203 is running when HA comes up
        await coordinator.async_setup()
        await coordinator._async_update_data()
        return coordinator.loco_states

    states = asyncio.run(scenario())
    assert set(states) == {11, 12}
    assert states[12].speed == 40


def test_system_state_push_does_not_postpone_keepalive():
    """A pushed System State must not reset the keepalive timer.

    The Z21 pushes LAN_SYSTEMSTATE_DATACHANGED every few seconds. Routing it
    through ``async_set_updated_data`` rescheduled the 30 s refresh on every
    push, so the keepalive (and its loco re-poll) never ran.
    """
    async def scenario():
        z21 = FakeZ21()
        coordinator = _make_coordinator(z21, asyncio.get_running_loop())
        await coordinator.async_setup()
        coordinator._handle_message(HDR_SYSTEMSTATE_DATACHANGED, _system_state())
        return coordinator

    coordinator = asyncio.run(scenario())
    coordinator.async_set_updated_data.assert_not_called()
    assert coordinator.data == _system_state()
    coordinator.async_update_listeners.assert_called()
