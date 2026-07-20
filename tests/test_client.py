"""Seam-2 suite for the async UDP client and its codec additions.

Verifies the header-keyed split primitive and the serial/hwinfo decoders, then
the client's symmetric I/O seam (ADR-0001): the send primitive, header-routed
receive dispatch to subscribers, the connect round-trip with retry/backoff and
single-drop tolerance, and a clean LAN_LOGOFF on close. Everything runs against
a faked transport — no physical Z21 and no real socket. Async coroutines are
driven with ``asyncio.run`` to keep the zero-dependency stance (no
pytest-asyncio).
"""

from __future__ import annotations

import asyncio
import struct
from pathlib import Path

import pytest

from custom_components.z21 import client as client_mod, protocol
from custom_components.z21.client import Z21Client, Z21Timeout, _Z21DatagramProtocol


def run(coro):
    return asyncio.run(coro)


# --- Fakes ------------------------------------------------------------------


class FakeTransport:
    """Records outbound datagrams; never touches a socket."""

    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self.closed = False

    def sendto(self, data: bytes, addr: object = None) -> None:
        self.sent.append(data)

    def close(self) -> None:
        self.closed = True


class RespondingTransport(FakeTransport):
    """Fake transport that feeds scripted responses back into the client.

    ``responder(header, client)`` is invoked after each send with the header of
    the request just sent; it may call ``client._on_datagram(...)`` to simulate
    the Z21 replying. Returning without feeding anything simulates a drop.
    """

    def __init__(self, client: Z21Client, responder) -> None:
        super().__init__()
        self._client = client
        self._responder = responder

    def sendto(self, data: bytes, addr: object = None) -> None:
        super().sendto(data)
        header = int.from_bytes(data[2:4], "little")
        self._responder(header, self._client)


def _serial_response(serial: int) -> bytes:
    return protocol.build_frame(protocol.HDR_SERIAL_NUMBER, struct.pack("<I", serial))


def _hwinfo_response(hw: int, fw: int) -> bytes:
    return protocol.build_frame(protocol.HDR_HWINFO, struct.pack("<II", hw, fw))


# --- Codec additions --------------------------------------------------------


def test_split_datasets_returns_header_payload_pairs():
    dgram = _serial_response(0xAABBCCDD) + _hwinfo_response(0x200, 0x123)
    pairs = protocol.split_datasets(dgram)
    assert pairs == [
        (protocol.HDR_SERIAL_NUMBER, struct.pack("<I", 0xAABBCCDD)),
        (protocol.HDR_HWINFO, struct.pack("<II", 0x200, 0x123)),
    ]


def test_split_datasets_skips_malformed_framing():
    # DataLen=0x14 (20) but only a few bytes follow -> overrun, walk stops.
    overrun = struct.pack("<HH", 0x14, protocol.HDR_SERIAL_NUMBER) + b"\x00\x00"
    assert protocol.split_datasets(overrun) == []
    # DataLen < 4 is malformed framing.
    too_small = struct.pack("<HH", 0x02, protocol.HDR_SERIAL_NUMBER)
    assert protocol.split_datasets(too_small) == []


def test_decode_serial_number():
    (header, payload), = protocol.split_datasets(_serial_response(123456))
    decoded = protocol.RECEIVE_DISPATCH[header](payload)
    assert isinstance(decoded, protocol.SerialNumber)
    assert decoded.serial == 123456


def test_decode_serial_number_short_returns_none():
    assert protocol._decode_serial_number(b"\x01\x02\x03") is None


def test_decode_hwinfo():
    (header, payload), = protocol.split_datasets(_hwinfo_response(0x200, 0x143))
    decoded = protocol.RECEIVE_DISPATCH[header](payload)
    assert isinstance(decoded, protocol.HwInfo)
    assert decoded.hw_type == 0x200
    assert decoded.fw_version == 0x143


def test_decode_hwinfo_short_returns_none():
    assert protocol._decode_hwinfo(struct.pack("<I", 0x200)) is None


def test_parse_datagram_unchanged_after_refactor():
    # SystemState-only contract preserved; serial/hwinfo are NOT SystemState.
    payload = struct.pack("<hhhhHH", 5, 0, 0, 0, 0, 0) + bytes([0, 0, 0, 1])
    dgram = (
        _serial_response(1)
        + protocol.build_frame(protocol.HDR_SYSTEMSTATE_DATACHANGED, payload)
        + _hwinfo_response(0x200, 1)
    )
    states = protocol.parse_datagram(dgram)
    assert len(states) == 1
    assert states[0].main_current == 5


# --- Send seam --------------------------------------------------------------


def test_send_frames_via_build_frame():
    c = Z21Client("192.0.2.10")
    t = FakeTransport()
    c._attach_transport(t)
    c.request_systemstate()
    assert t.sent == [protocol.build_systemstate_getdata()]


def test_send_without_transport_raises():
    c = Z21Client("192.0.2.10")
    with pytest.raises(RuntimeError):
        c.send(protocol.HDR_SYSTEMSTATE_GETDATA)


def test_set_broadcastflags_default_bytes():
    c = Z21Client("192.0.2.10")
    t = FakeTransport()
    c._attach_transport(t)
    c.set_broadcastflags()
    assert t.sent == [protocol.build_set_broadcastflags()]


# --- Receive seam -----------------------------------------------------------


def test_subscribe_receives_decoded_by_header():
    c = Z21Client("192.0.2.10")
    received: list[tuple[int, object]] = []
    unsub = c.subscribe(lambda h, d: received.append((h, d)))

    payload = struct.pack("<hhhhHH", 7, 0, 0, 0, 0, 0) + bytes([0, 0, 0, 1])
    c._on_datagram(protocol.build_frame(protocol.HDR_SYSTEMSTATE_DATACHANGED, payload))

    assert len(received) == 1
    header, decoded = received[0]
    assert header == protocol.HDR_SYSTEMSTATE_DATACHANGED
    assert isinstance(decoded, protocol.SystemState)
    assert decoded.main_current == 7

    unsub()
    c._on_datagram(protocol.build_frame(protocol.HDR_SYSTEMSTATE_DATACHANGED, payload))
    assert len(received) == 1  # no further delivery after unsubscribe


def test_datagram_received_routes_to_client():
    c = Z21Client("192.0.2.10")
    received: list[tuple[int, object]] = []
    c.subscribe(lambda h, d: received.append((h, d)))
    proto = _Z21DatagramProtocol(c)
    proto.datagram_received(_serial_response(42), ("192.0.2.10", 21105))
    assert received == [(protocol.HDR_SERIAL_NUMBER, protocol.SerialNumber(42))]


def test_combined_datagram_dispatched_per_header():
    c = Z21Client("192.0.2.10")
    received: list[int] = []
    c.subscribe(lambda h, d: received.append(h))
    c._on_datagram(_serial_response(1) + _hwinfo_response(0x200, 1))
    assert received == [protocol.HDR_SERIAL_NUMBER, protocol.HDR_HWINFO]


def test_handler_exception_does_not_break_transport():
    c = Z21Client("192.0.2.10")
    seen: list[int] = []

    def boom(h, d):
        raise ValueError("handler blew up")

    c.subscribe(boom)
    c.subscribe(lambda h, d: seen.append(h))
    # Must not raise even though the first handler does.
    c._on_datagram(_serial_response(1))
    assert seen == [protocol.HDR_SERIAL_NUMBER]


# --- connect ----------------------------------------------------------------


def test_connect_roundtrips_serial_and_hwinfo():
    async def scenario():
        c = Z21Client("192.0.2.10")

        def responder(header, client):
            if header == protocol.HDR_SERIAL_NUMBER:
                client._on_datagram(_serial_response(0xABCD))
            elif header == protocol.HDR_HWINFO:
                client._on_datagram(_hwinfo_response(0x200, 0x143))

        c._attach_transport(RespondingTransport(c, responder))
        return await c.connect(timeout=0.5)

    serial, hwinfo = run(scenario())
    assert serial == protocol.SerialNumber(0xABCD)
    assert hwinfo == protocol.HwInfo(0x200, 0x143)


def test_connect_tolerates_single_dropped_datagram():
    async def scenario():
        c = Z21Client("192.0.2.10")
        state = {"serial_seen": 0}

        def responder(header, client):
            if header == protocol.HDR_SERIAL_NUMBER:
                state["serial_seen"] += 1
                # Drop the FIRST serial response; answer on the retry.
                if state["serial_seen"] >= 2:
                    client._on_datagram(_serial_response(0xABCD))
            elif header == protocol.HDR_HWINFO:
                client._on_datagram(_hwinfo_response(0x200, 1))

        transport = RespondingTransport(c, responder)
        c._attach_transport(transport)
        result = await c.connect(timeout=0.05, retries=3, backoff=0.01)
        return result, state["serial_seen"]

    (serial, hwinfo), serial_seen = run(scenario())
    assert serial == protocol.SerialNumber(0xABCD)
    assert serial_seen == 2  # retry actually re-sent the serial request


def test_connect_times_out_raises_z21timeout():
    async def scenario():
        c = Z21Client("192.0.2.10")
        t = FakeTransport()  # never responds
        c._attach_transport(t)
        with pytest.raises(Z21Timeout):
            await c.connect(timeout=0.02, retries=3, backoff=0.0)
        # One serial + one hwinfo request per attempt.
        return t.sent

    sent = run(scenario())
    serial_reqs = sent.count(protocol.build_get_serial_number())
    hwinfo_reqs = sent.count(protocol.build_get_hwinfo())
    assert serial_reqs == 3
    assert hwinfo_reqs == 3


# --- close ------------------------------------------------------------------


def test_close_sends_logoff_and_tears_down():
    async def scenario():
        c = Z21Client("192.0.2.10")
        t = FakeTransport()
        c._attach_transport(t)
        await c.close()
        return c, t

    c, t = run(scenario())
    assert t.sent[-1] == protocol.build_logoff()
    assert t.closed is True
    assert c._transport is None


def test_close_idempotent():
    async def scenario():
        c = Z21Client("192.0.2.10")
        await c.close()  # never opened
        t = FakeTransport()
        c._attach_transport(t)
        await c.close()
        await c.close()  # already closed
        return t

    t = run(scenario())
    assert t.closed is True
    assert t.sent.count(protocol.build_logoff()) == 1


def test_error_received_is_non_fatal():
    c = Z21Client("192.0.2.10")
    t = FakeTransport()
    c._attach_transport(t)
    proto = _Z21DatagramProtocol(c)
    proto.error_received(OSError("icmp port unreachable"))
    # Endpoint stays usable.
    c.request_serial_number()
    assert t.sent == [protocol.build_get_serial_number()]


# --- Seam guard: no HA / socket imports -------------------------------------


def test_client_has_no_forbidden_imports():
    src = Path(client_mod.__file__).read_text()
    for forbidden in ("import socket", "homeassistant"):
        assert forbidden not in src, f"client.py must not reference {forbidden!r}"
