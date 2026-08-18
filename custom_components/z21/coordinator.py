"""System State coordinator for the Z21 integration.

Owns the single live :class:`Z21Client` UDP endpoint for a config entry and turns
the Z21's push model into a Home Assistant ``DataUpdateCoordinator``:

- On setup it round-trips the serial+hwinfo handshake, subscribes to the **System
  State** broadcast group (``LAN_SET_BROADCASTFLAGS`` flag ``0x00000100``, spec
  2.16), and registers a receive handler.
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
are re-sent (they reset on the Z21's logoff/reconnect), so a power-cycled Z21
recovers without reloading the integration.

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
from .client import Z21Client, Z21Timeout
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# 30 s keepalive per issue #5; a poll awaits its reply for _STATE_TIMEOUT.
# STALENESS_WINDOW (~75 s = 2.5× keepalive, issue #8) is how long the Z21 may go
# silent before entities are marked unavailable — a single missed poll is
# tolerated. Module-level so tests can shrink them.
KEEPALIVE_INTERVAL = 30.0
_STATE_TIMEOUT = 5.0
STALENESS_WINDOW = 2.5 * KEEPALIVE_INTERVAL


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
        self._unsub: Callable[[], None] | None = None
        # Set while a poll awaits its reply; the receive handler resolves it.
        self._waiter: asyncio.Future[protocol.SystemState] | None = None
        # Monotonic time of the last received System State (push or poll reply);
        # None until the first ever datagram. Drives the staleness window.
        self._last_rx: float | None = None
        # True while past the staleness window, so the recovery edge (re-send of
        # broadcast flags on the first datagram after silence) fires exactly once.
        self._stale: bool = False
        # Maps turnout index (int) to position (int: 0=closed/straight, 1=diverged/curved, None=not switched yet).
        self._turnout_positions: dict[int, int | None] = {}

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

    def _handle_message(self, header: int, decoded: object) -> None:
        """Route a decoded dataset; System State updates entities, TurnoutInfo updates positions."""
        if header == protocol.HDR_SYSTEMSTATE_DATACHANGED and isinstance(
            decoded, protocol.SystemState
        ):
            self._last_rx = self.hass.loop.time()
            if self._stale:
                self.client.set_broadcastflags(
                    protocol.BROADCAST_FLAG_SYSTEM_STATE
                    | protocol.BROADCAST_FLAG_DRIVING_SWITCHING
                )
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

    @property
    def turnout_positions(self) -> dict[int, int | None]:
        """Return a copy of the last known turnout positions (FAdr -> position)."""
        return dict(self._turnout_positions)

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