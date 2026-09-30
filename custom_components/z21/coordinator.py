"""System State coordinator for the Z21 integration.

Owns the single live :class:`Z21Client` UDP endpoint for a config entry and turns
the Z21's push model into a Home Assistant ``DataUpdateCoordinator``:

- On setup it round-trips the serial+hwinfo handshake, subscribes to the **System
  State** broadcast group (``LAN_SET_BROADCASTFLAGS`` flag ``0x00000100``, spec
  2.16), registers a receive handler, and polls the initial position of every
  configured turnout so their states are known without waiting for the first
  throw. Every configured loco is likewise polled **and subscribed** with
  ``LAN_X_GET_LOCO_INFO`` (spec 4.1) so its ``LAN_X_LOCO_INFO`` feedback arrives
  (ADR-0003).
- A pushed ``LAN_SYSTEMSTATE_DATACHANGED`` (spec 2.18) is fed straight to entities
  via ``async_set_updated_data``.
- The 30 s poll (``LAN_SYSTEMSTATE_GETDATA``, spec 2.19) doubles as a keepalive
  and a staleness detector: its reply *is* a ``LAN_SYSTEMSTATE_DATACHANGED``, so
  it shares the receive path.

Liveness is tracked by the time of the last received datagram (push *or* poll
reply), not by any single poll's success. A missed poll is tolerated while a
datagram arrived within the **staleness window** (~2.5× keepalive); only silence
past that window surfaces as ``UpdateFailed`` (and, via
``async_config_entry_first_refresh``, ``ConfigEntryNotReady`` on setup), greying
out the entities. On the first datagram after such a silence the broadcast flags
are re-sent (they reset on the Z21's logoff/reconnect), every configured
turnout is re-polled and every configured loco re-subscribed, so a power-cycled
Z21 recovers its turnout and loco states without reloading the integration.

This is the first layer with a Home Assistant dependency below the config flow;
the transport (``client``) and codec (``protocol``) stay HA-free.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import protocol
from .client import TURNOUT_DEACTIVATE_DELAY, Z21Client, Z21Timeout
from .const import (
    CONF_LOCO_ADDRESS,
    CONF_LOCO_SPEED_STEPS,
    CONF_LOCOS,
    CONF_TURNOUT_FADR,
    CONF_TURNOUTS,
    DOMAIN,
    LOCO_SPEED_STEPS_DEFAULT,
)

_LOGGER = logging.getLogger(__name__)

# 30 s keepalive per issue #5; a poll awaits its reply for _STATE_TIMEOUT.
# STALENESS_WINDOW (~75 s = 2.5× keepalive, issue #8) is how long the Z21 may go
# silent before entities are marked unavailable — a single missed poll is
# tolerated. Module-level so tests can shrink them.
KEEPALIVE_INTERVAL = 30.0
_STATE_TIMEOUT = 5.0
STALENESS_WINDOW = 2.5 * KEEPALIVE_INTERVAL

# After a throw the client sends Activate now and Deactivate after
# TURNOUT_DEACTIVATE_DELAY; wait past that pair before re-polling so the Z21 has
# committed the new position and doesn't answer with the stale one. Module-level
# so tests can shrink it.
TURNOUT_SETTLE_DELAY = TURNOUT_DEACTIVATE_DELAY + 0.1


class Z21Coordinator(DataUpdateCoordinator[protocol.SystemState]):
    """Owns the live Z21 client and the latest System State for one entry."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: Z21Client
    ) -> None:
        self.config_entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=KEEPALIVE_INTERVAL),
        )
        self.client = client
        # Device-registry id of the station Device, set by setup before the
        # platforms are forwarded; loco Devices nest under it (via_device_id).
        self.station_device_id: str | None = None
        self._unsub: Callable[[], None] | None = None
        # Set while a poll awaits its reply; the receive handler resolves it.
        self._waiter: asyncio.Future[protocol.SystemState] | None = None
        # Monotonic time of the last received System State (push or poll reply);
        # None until the first ever datagram. Drives the staleness window.
        self._last_rx: float | None = None
        # True while past the staleness window, so the recovery edge (re-send of
        # broadcast flags on the first datagram after silence) fires exactly once.
        self._stale: bool = False
        # Maps turnout FAdr to position (0=output 1, 1=output 2, None=not
        # switched yet). The Z21 speaks only of outputs, not straight/branching.
        self._turnout_positions: dict[int, int | None] = {}
        # Loco address -> last LAN_X_LOCO_INFO the Z21 reported. Speed and
        # direction are one coupled wire command, so every drive command is
        # composed from this (ADR-0003); absent until the first feedback.
        self._loco_states: dict[int, protocol.LocoInfo] = {}

    async def async_setup(self) -> None:
        """Connect, subscribe to System State broadcasts, and start listening.

        Raises :class:`ConfigEntryNotReady` (retryable) if the handshake fails.
        """
        try:
            await self.client.connect()
        except (Z21Timeout, OSError) as err:
            await self.client.close()
            raise ConfigEntryNotReady(
                f"Z21 handshake failed: {err}"
            ) from err
        self.client.set_broadcastflags(
            protocol.BROADCAST_FLAG_SYSTEM_STATE
            | protocol.BROADCAST_FLAG_DRIVING_SWITCHING
        )
        self._unsub = self.client.subscribe(self._handle_message)
        self._discover_turnouts()
        self._discover_locos()

    def _discover_turnouts(self) -> None:
        """Poll the position of every configured turnout (LAN_X_GET_TURNOUT_INFO).

        Called when the Z21 becomes available — on setup and again on recovery
        from a stale/silent period, since the Z21 forgets its state model on
        logoff. Each reply arrives as a ``LAN_X_TURNOUT_INFO`` and updates
        :attr:`turnout_positions` via :meth:`_handle_message`.
        """
        for turnout in self.config_entry.options.get(CONF_TURNOUTS, []):
            self.client.request_turnout_info(turnout[CONF_TURNOUT_FADR])

    def _discover_locos(self) -> None:
        """Poll and subscribe every configured loco (LAN_X_GET_LOCO_INFO, 4.1).

        Called alongside :meth:`_discover_turnouts` — on setup and on recovery
        from silence, since the Z21 drops its per-client subscriptions on logoff.
        Replies and later changes arrive as ``LAN_X_LOCO_INFO`` and update
        :attr:`loco_states` via :meth:`_handle_message`.
        """
        for loco in self.config_entry.options.get(CONF_LOCOS, []):
            self.client.request_loco_info(loco[CONF_LOCO_ADDRESS])

    def _handle_message(self, header: int, decoded: object) -> None:
        """Route a decoded dataset to System State, turnout positions, or loco state."""
        if header == protocol.HDR_SYSTEMSTATE_DATACHANGED and isinstance(
            decoded, protocol.SystemState
        ):
            self._last_rx = self.hass.loop.time()
            if self._stale:
                self.client.set_broadcastflags(
                    protocol.BROADCAST_FLAG_SYSTEM_STATE
                    | protocol.BROADCAST_FLAG_DRIVING_SWITCHING
                )
                self._discover_turnouts()
                self._discover_locos()
                self._stale = False
            waiter = self._waiter
            if waiter is not None and not waiter.done():
                waiter.set_result(decoded)
            else:
                self.async_set_updated_data(decoded)
        elif header == protocol.HDR_TURNOUT_INFO and isinstance(
            decoded, protocol.TurnoutInfo
        ):
            self._turnout_positions[decoded.fadr] = decoded.position
            self.async_update_listeners()
        elif header == protocol.HDR_LOCO_INFO and isinstance(
            decoded, protocol.LocoInfo
        ):
            self._loco_states[decoded.address] = decoded
            self.async_update_listeners()

    @property
    def turnout_positions(self) -> dict[int, int | None]:
        """Return a copy of the last known turnout positions (FAdr -> position)."""
        return dict(self._turnout_positions)

    @property
    def loco_states(self) -> dict[int, protocol.LocoInfo]:
        """Return a copy of the last-known loco states (address -> LocoInfo)."""
        return dict(self._loco_states)

    def drive_loco(
        self,
        address: int,
        *,
        speed: int | None = None,
        forward: bool | None = None,
        estop: bool = False,
    ) -> None:
        """Send LAN_X_SET_LOCO_DRIVE (4.2), composing from last-known state.

        Speed and direction share one wire command, so whichever of ``speed`` /
        ``forward`` is omitted is taken from the loco's last reported
        ``LAN_X_LOCO_INFO`` — defaulting to forward, speed 0 before any feedback
        has arrived (ADR-0003). Always sends; state is **not** updated
        optimistically — it follows the Z21's subscription feedback.

        The command is sent in the step mode the Z21 *last reported* for this
        address, not the configured one. ``LAN_X_SET_LOCO_DRIVE`` (4.2) stores
        its ``S`` nibble as that address's mode, so driving in the configured
        mode (the slider's) rewrites a handset's 14/28-step loco into 128 and
        the decoder ignores the new speed. Direction and E-Stop still moved the
        loco because they re-encoded the speed the Z21 already had. An explicit
        ``speed`` is a raw step in the *configured* mode (the slider's range)
        and is rescaled into the reported mode; an omitted one is already in
        the reported mode. Before any feedback the configured mode is used.
        The step is clamped to the mode actually sent so it can never be
        encoded as an invalid code.
        """
        last = self._loco_states.get(address)
        configured = self._loco_speed_steps(address)
        speed_steps = last.speed_steps if last is not None else configured
        if speed is None:
            speed = last.speed if last is not None else 0
        elif last is not None and last.speed_steps != configured:
            speed = protocol.rescale_speed_step(speed, configured, speed_steps)
        if forward is None:
            forward = last.forward if last is not None else True
        self.client.set_loco_drive(
            address,
            step=max(0, min(speed, protocol.max_speed_step(speed_steps))),
            forward=forward,
            speed_steps=speed_steps,
            estop=estop,
        )

    def _loco_speed_steps(self, address: int) -> int:
        """Return the configured speed-step mode for ``address`` (default 128)."""
        for loco in self.config_entry.options.get(CONF_LOCOS, []):
            if loco[CONF_LOCO_ADDRESS] == address:
                return loco.get(CONF_LOCO_SPEED_STEPS, LOCO_SPEED_STEPS_DEFAULT)
        return LOCO_SPEED_STEPS_DEFAULT

    async def async_refresh_turnout(self, fadr: int) -> None:
        """Re-poll a turnout's position after a throw settles (LAN_X_GET_TURNOUT_INFO, 5.1).

        The Z21 sends no unsolicited position update, so after commanding a throw
        we query it once the Activate/Deactivate pair has completed. The reply
        arrives as a ``LAN_X_TURNOUT_INFO`` and updates :attr:`turnout_positions`
        via :meth:`_handle_message`, exactly like the setup/recovery discovery
        poll — keeping turnout state non-optimistic (the Z21 is the source of
        truth), consistent with the track-power switch (ADR-0002).
        """
        await asyncio.sleep(TURNOUT_SETTLE_DELAY)
        self.client.request_turnout_info(fadr)

    async def _async_update_data(self) -> protocol.SystemState:
        """Poll for System State, awaiting the pushed reply within the window."""
        loop = self.hass.loop
        waiter: asyncio.Future[protocol.SystemState] = loop.create_future()
        self._waiter = waiter
        try:
            self.client.request_systemstate()
            return await asyncio.wait_for(waiter, _STATE_TIMEOUT)
        except (asyncio.TimeoutError, TimeoutError) as err:
            # A missed poll is tolerated while a datagram arrived within the
            # staleness window — keep the last known state and stay available.
            now = self.hass.loop.time()
            if self._last_rx is not None and now - self._last_rx <= STALENESS_WINDOW:
                return self.data
            self._stale = True
            raise UpdateFailed(
                "No System State from Z21 within staleness window"
            ) from err
        finally:
            self._waiter = None

    async def async_shutdown_client(self) -> None:
        """Unsubscribe and close the live client (on unload)."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        await self.client.close()