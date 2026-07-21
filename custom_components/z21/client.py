"""Async UDP client for a Z21 command station.

The Home-Assistant-free transport layer built on the pure codec (``protocol``):
it wraps a single ``asyncio.DatagramProtocol`` UDP endpoint (port 21105) and
realizes the symmetric I/O seam of ADR-0001 —

- **Send path**: a general :meth:`Z21Client.send` ``(header, payload)`` primitive
  over the one endpoint; v1 outbound messages are thin wrappers on it, and future
  control commands are new wrappers on the same seam.
- **Receive path**: inbound datagrams are split, decoded by ``Header`` through
  ``protocol.RECEIVE_DISPATCH``, and dispatched to registered handlers. Adding a
  control-related inbound message later is a new dispatch entry plus a handler —
  no transport rework.

There is deliberately no Home Assistant import here; keepalive scheduling, the
staleness window, and broadcast-flag re-send-on-reconnect belong to the later HA
coordinator, not this reusable transport.
"""

from __future__ import annotations

import asyncio
import logging
import struct
from collections.abc import Callable

from custom_components.z21 import protocol

DEFAULT_PORT = 21105

_LOGGER = logging.getLogger(__name__)

# A receive handler: called with the decoded dataset's header and the decoded
# object (e.g. protocol.SystemState) for every successfully decoded datagram.
Handler = Callable[[int, object], None]


class Z21Timeout(Exception):
    """``connect`` exhausted its retries without a serial + hwinfo response."""


class _Z21DatagramProtocol(asyncio.DatagramProtocol):
    """Single UDP endpoint: routes raw datagrams into the owning client."""

    def __init__(self, client: "Z21Client") -> None:
        self._client = client

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._client._attach_transport(transport)

    def datagram_received(self, data: bytes, addr: object) -> None:
        self._client._on_datagram(data)

    def error_received(self, exc: Exception) -> None:
        # UDP delivery errors are non-fatal — log and keep the endpoint open.
        _LOGGER.debug("Z21 UDP error_received: %s", exc)

    def connection_lost(self, exc: Exception | None) -> None:
        self._client._on_connection_lost()


class Z21Client:
    """Async UDP client for one Z21 command station (Home-Assistant-free).

    Wraps the pure codec in a single ``asyncio.DatagramProtocol`` endpoint.
    Sends via the general :meth:`send` ``(header, payload)`` primitive; decodes
    inbound datagrams and dispatches them by header to registered handlers.
    """

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._loop = loop
        self._transport: asyncio.BaseTransport | None = None
        self._subscribers: list[Handler] = []
        # Header -> one-shot future awaiting the next response with that header.
        # The Z21 has no request IDs, so responses correlate only by header.
        self._pending: dict[int, asyncio.Future] = {}

    # --- Lifecycle ----------------------------------------------------------

    async def open(self) -> None:
        """Open the UDP endpoint to the Z21. Idempotent."""
        if self._transport is not None:
            return
        loop = self._loop or asyncio.get_running_loop()
        transport, _protocol = await loop.create_datagram_endpoint(
            lambda: _Z21DatagramProtocol(self),
            remote_addr=(self._host, self._port),
        )
        # connection_made already stored the transport, but assign defensively
        # in case a fake transport bypasses that callback.
        self._transport = transport

    async def connect(
        self,
        *,
        timeout: float = 2.0,
        retries: int = 3,
        backoff: float = 0.5,
    ) -> tuple[protocol.SerialNumber, protocol.HwInfo]:
        """Round-trip serial + hwinfo, returning both.

        Opens the endpoint if needed, then on each attempt re-sends both
        requests and awaits their responses (correlated by header) within
        ``timeout``. A failed attempt sleeps ``backoff * 2**attempt`` before
        retrying, so a single dropped datagram against a reachable Z21 is
        recovered on the next attempt. Raises :class:`Z21Timeout` once all
        ``retries`` attempts are exhausted.
        """
        await self.open()
        loop = self._loop or asyncio.get_running_loop()
        last_exc: BaseException | None = None

        for attempt in range(retries):
            serial_fut: asyncio.Future = loop.create_future()
            hwinfo_fut: asyncio.Future = loop.create_future()
            self._pending[protocol.HDR_SERIAL_NUMBER] = serial_fut
            self._pending[protocol.HDR_HWINFO] = hwinfo_fut
            try:
                self.request_serial_number()
                self.request_hwinfo()
                serial, hwinfo = await asyncio.wait_for(
                    asyncio.gather(serial_fut, hwinfo_fut), timeout
                )
                return serial, hwinfo
            except (asyncio.TimeoutError, TimeoutError) as exc:
                last_exc = exc
                if attempt < retries - 1:
                    await asyncio.sleep(backoff * (2**attempt))
            finally:
                self._pending.pop(protocol.HDR_SERIAL_NUMBER, None)
                self._pending.pop(protocol.HDR_HWINFO, None)

        raise Z21Timeout(
            f"No serial+hwinfo from {self._host}:{self._port} "
            f"after {retries} attempts"
        ) from last_exc

    async def close(self) -> None:
        """Send ``LAN_LOGOFF`` (best effort) and tear down the endpoint.

        Idempotent — safe to call when never opened or already closed.
        """
        if self._transport is None:
            return
        try:
            self.logoff()
        except Exception:  # pragma: no cover - defensive
            _LOGGER.debug("Z21 logoff during close failed", exc_info=True)
        self._transport.close()
        self._transport = None

    # --- Send seam (ADR-0001) ----------------------------------------------

    def send(self, header: int, payload: bytes = b"") -> None:
        """Frame and send ``payload`` under ``header`` — the send primitive."""
        self._transport_send(protocol.build_frame(header, payload))

    def _transport_send(self, frame: bytes) -> None:
        """Send a complete framed datagram — the single transport touch point."""
        if self._transport is None:
            raise RuntimeError("Z21Client endpoint not open")
        self._transport.sendto(frame)

    def request_serial_number(self) -> None:
        """Send LAN_GET_SERIAL_NUMBER (2.1)."""
        self.send(protocol.HDR_SERIAL_NUMBER)

    def request_hwinfo(self) -> None:
        """Send LAN_GET_HWINFO (2.20)."""
        self.send(protocol.HDR_HWINFO)

    def request_systemstate(self) -> None:
        """Send LAN_SYSTEMSTATE_GETDATA (2.19)."""
        self.send(protocol.HDR_SYSTEMSTATE_GETDATA)

    def set_broadcastflags(
        self, flags: int = protocol.BROADCAST_FLAG_SYSTEM_STATE
    ) -> None:
        """Send LAN_SET_BROADCASTFLAGS (2.16), defaulting to system state."""
        self.send(protocol.HDR_SET_BROADCASTFLAGS, struct.pack("<I", flags))

    def set_track_power_on(self) -> None:
        """Send LAN_X_SET_TRACK_POWER_ON (2.6)."""
        self._transport_send(protocol.build_track_power_on())

    def set_track_power_off(self) -> None:
        """Send LAN_X_SET_TRACK_POWER_OFF (2.5)."""
        self._transport_send(protocol.build_track_power_off())

    def emergency_stop(self) -> None:
        """Send LAN_X_SET_STOP (2.13) — halt all locos, leave track power on."""
        self._transport_send(protocol.build_set_stop())

    def logoff(self) -> None:
        """Send LAN_LOGOFF (2.2)."""
        self.send(protocol.HDR_LOGOFF)

    # --- Receive seam -------------------------------------------------------

    def subscribe(self, handler: Handler) -> Callable[[], None]:
        """Register ``handler(header, decoded)``; returns an unsubscribe callable."""
        self._subscribers.append(handler)

        def _unsubscribe() -> None:
            try:
                self._subscribers.remove(handler)
            except ValueError:
                pass

        return _unsubscribe

    def _on_datagram(self, data: bytes) -> None:
        """Decode an inbound UDP payload and route each dataset by header."""
        for header, payload in protocol.split_datasets(data):
            decoder = protocol.RECEIVE_DISPATCH.get(header)
            if decoder is None:
                continue
            decoded = decoder(payload)
            if decoded is None:
                continue

            fut = self._pending.get(header)
            if fut is not None and not fut.done():
                fut.set_result(decoded)

            for handler in list(self._subscribers):
                try:
                    handler(header, decoded)
                except Exception:  # a handler must never break the transport
                    _LOGGER.exception("Z21 receive handler failed")

    def _on_connection_lost(self) -> None:
        self._transport = None

    # --- Test seam ----------------------------------------------------------

    def _attach_transport(self, transport: asyncio.BaseTransport) -> None:
        """Attach a transport directly (used by connection_made and tests)."""
        self._transport = transport
