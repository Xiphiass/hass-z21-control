"""Pure Z21 LAN protocol codec.

The Home-Assistant-free and socket-free foundation of the client library: it
builds v1 outbound messages to exact bytes and parses inbound UDP datagrams into
decoded datasets. There is deliberately no ``asyncio`` transport and no Home
Assistant import here (see ADR-0001, the symmetric I/O seam) so this module can
be exercised by a pure protocol-compliance test suite and reused unchanged when
transport and HA platforms are layered on later.

Every Z21 datagram is framed as::

    DataLen (LE16) | Header (LE16) | Data

where ``DataLen`` counts the whole dataset (the two length bytes, the two header
bytes, and the data). Multiple datasets may be packed into a single UDP packet.

Byte layouts and bitmasks follow the Z21 LAN protocol specification v1.13
(sections 2.1, 2.2, 2.16, 2.18, 2.19, 2.20).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntFlag

# --- Headers (little-endian 16-bit on the wire) -----------------------------

# Outbound (client -> Z21)
HDR_SERIAL_NUMBER = 0x10  # LAN_GET_SERIAL_NUMBER (2.1)
HDR_HWINFO = 0x1A  # LAN_GET_HWINFO (2.20)
HDR_LOGOFF = 0x30  # LAN_LOGOFF (2.2)
HDR_SET_BROADCASTFLAGS = 0x50  # LAN_SET_BROADCASTFLAGS (2.16)
HDR_SYSTEMSTATE_GETDATA = 0x85  # LAN_SYSTEMSTATE_GETDATA (2.19)
HDR_X = 0x40  # LAN_X (X-bus tunnel; carries e.g. LAN_X_SET_TRACK_POWER_*)

# Inbound (Z21 -> client)
HDR_SYSTEMSTATE_DATACHANGED = 0x84  # LAN_SYSTEMSTATE_DATACHANGED (2.18)
# NOTE: 0x43 is the *X-Header* of LAN_X_TURNOUT_INFO (5.3), not a top-level
# Header — the message arrives framed under HDR_X (0x40). We keep it as the
# stable logical routing key that ``decode_xbus`` surfaces turnout info under
# (see ``_XBUS_DISPATCH``), so the client's pending-future dict and the
# coordinator can key on it directly.
HDR_TURNOUT_INFO = 0x43  # LAN_X_TURNOUT_INFO X-Header (5.3)

# --- Broadcast flags (2.16) -------------------------------------------------

# The System State broadcast group: delivers LAN_SYSTEMSTATE_DATACHANGED.
# NOTE: 0x00000001 is the *driving & switching* group, NOT system state — a
# common mix-up. v1 subscribes only to system state.
BROADCAST_FLAG_SYSTEM_STATE = 0x00000100
BROADCAST_FLAG_DRIVING_SWITCHING = 0x00000001


class CentralState(IntFlag):
    """SystemState.CentralState bitmask (2.18)."""

    EMERGENCY_STOP = 0x01  # csEmergencyStop
    TRACK_VOLTAGE_OFF = 0x02  # csTrackVoltageOff
    SHORT_CIRCUIT = 0x04  # csShortCircuit
    PROGRAMMING_MODE_ACTIVE = 0x20  # csProgrammingModeActive


class CentralStateEx(IntFlag):
    """SystemState.CentralStateEx bitmask (2.18)."""

    HIGH_TEMPERATURE = 0x01  # cseHighTemperature
    POWER_LOST = 0x02  # csePowerLost
    SHORT_CIRCUIT_EXTERNAL = 0x04  # cseShortCircuitExternal
    SHORT_CIRCUIT_INTERNAL = 0x08  # cseShortCircuitInternal
    RCN213 = 0x20  # cseRCN213 (Z21 FW >= 1.42)


class Capabilities(IntFlag):
    """SystemState.Capabilities bitmask (2.18, Z21 FW >= 1.42).

    Only meaningful when nonzero: a zero byte indicates older firmware whose
    capabilities must not be evaluated (see ``SystemState.capabilities_valid``).
    """

    DCC = 0x01  # capDCC
    MM = 0x02  # capMM
    RAILCOM = 0x08  # capRailCom
    LOCO_CMDS = 0x10  # capLocoCmds
    ACCESSORY_CMDS = 0x20  # capAccessoryCmds
    DETECTOR_CMDS = 0x40  # capDetectorCmds
    NEEDS_UNLOCK_CODE = 0x80  # capNeedsUnlockCode


# --- Send path: general framing primitive + v1 outbound builders ------------


def build_frame(header: int, payload: bytes = b"") -> bytes:
    """Frame ``payload`` under ``header`` — the general ``send(header, payload)``.

    Prepends ``DataLen (LE16)`` (total dataset length = payload + 4 framing
    bytes) and ``Header (LE16)``. Every outbound builder is a thin wrapper on
    this primitive; future control commands are new builders on the same seam.
    """
    return struct.pack("<HH", len(payload) + 4, header) + payload


def build_get_serial_number() -> bytes:
    """LAN_GET_SERIAL_NUMBER request (2.1) -> ``04 00 10 00``."""
    return build_frame(HDR_SERIAL_NUMBER)


def build_get_hwinfo() -> bytes:
    """LAN_GET_HWINFO request (2.20) -> ``04 00 1A 00``."""
    return build_frame(HDR_HWINFO)


def build_logoff() -> bytes:
    """LAN_LOGOFF request (2.2) -> ``04 00 30 00``."""
    return build_frame(HDR_LOGOFF)


def build_systemstate_getdata() -> bytes:
    """LAN_SYSTEMSTATE_GETDATA request (2.19) -> ``04 00 85 00``."""
    return build_frame(HDR_SYSTEMSTATE_GETDATA)


def build_set_broadcastflags(flags: int = BROADCAST_FLAG_SYSTEM_STATE) -> bytes:
    """LAN_SET_BROADCASTFLAGS request (2.16).

    Default subscribes to the System State group only ->
    ``08 00 50 00 00 01 00 00``.
    """
    return build_frame(HDR_SET_BROADCASTFLAGS, struct.pack("<I", flags))


def build_xbus(x_header: int, db: bytes = b"") -> bytes:
    """Frame an X-bus command under ``HDR_X`` (LAN_X, 5.x).

    The X-bus payload is ``X-Header | DB0.. | XOR-Byte``, where the trailing
    checkbyte is the XOR of the X-header and every data byte. This is the shared
    control-send primitive; each LAN_X command is a thin wrapper on it.
    """
    xbus = bytes((x_header,)) + db
    checksum = 0
    for byte in xbus:
        checksum ^= byte
    return build_frame(HDR_X, xbus + bytes((checksum,)))


def build_track_power_off() -> bytes:
    """LAN_X_SET_TRACK_POWER_OFF (2.5) -> ``07 00 40 00 21 80 A1``."""
    return build_xbus(0x21, b"\x80")


def build_track_power_on() -> bytes:
    """LAN_X_SET_TRACK_POWER_ON (2.6) -> ``07 00 40 00 21 81 A0``."""
    return build_xbus(0x21, b"\x81")


def build_set_stop() -> bytes:
    """LAN_X_SET_STOP (2.13) -> ``06 00 40 00 80 80``.

    Emergency stop: halts all locos but leaves track voltage on (distinct from
    track-power-off). The X-bus command is the lone X-header ``0x80`` with no
    data byte, so the XOR checkbyte is ``0x80`` itself.
    """
    return build_xbus(0x80)


def build_turnout_info_get(fadr: int) -> bytes:
    """LAN_X_GET_TURNOUT_INFO request (5.1).

    Polls the position of a turnout by its function address.
    ``fadr`` is the raw FAdr value (e.g. 0, 4, 9, ...).

    Example for FAdr=4::

        08 00 40 00 43 00 04 47

    """
    fadr_ms = (fadr >> 8) & 0xFF
    fadr_ls = fadr & 0xFF
    return build_xbus(0x43, bytes((fadr_ms, fadr_ls)))


def build_turnout_set(
    fadr: int, output: int, activate: bool, q: bool = True
) -> bytes:
    """LAN_X_SET_TURNOUT command (5.2).

    Switches a turnout by its function address. DB2 is ``10Q0A00P`` where A and
    P are independent bits: A activates (1) or deactivates (0) the selected
    output, and P selects output 1 (``0``) or output 2 (``1``). Throwing a
    turnout is therefore two commands — Activate the chosen output, then
    Deactivate it (spec 5.2.1); the client owns that pairing and its timing.

    Args:
        fadr: Raw function address (0–65534).
        output: 0 = output 1, 1 = output 2 (the P bit).
        activate: True activates the output (A=1), False deactivates it (A=0).
        q: Queue mode (spec 5.2.2, Z21 FW 1.24+). Defaults to True — the
            integration always uses the queue so it need not strictly serialize
            switching commands across turnouts.

    Example for FAdr=4, output=1 (output 2), activate, Q=1::

        09 00 40 00 53 00 04 A9 FE

    """
    fadr_ms = (fadr >> 8) & 0xFF
    fadr_ls = fadr & 0xFF
    q_bit = 1 if q else 0
    a_bit = 1 if activate else 0
    db2 = 0x80 | (q_bit << 5) | (a_bit << 3) | (output & 0x01)
    return build_xbus(0x53, bytes((fadr_ms, fadr_ls, db2)))


def build_turnout_info(fadr: int, zz: int) -> bytes:
    """LAN_X_TURNOUT_INFO datagram as the Z21 sends it (5.3).

    The inbound counterpart to :func:`build_turnout_info_get`: frames the reply
    under ``HDR_X`` with X-Header ``0x43`` and DB2 ``000000ZZ``. Provided so
    tests (and any round-trip) exercise the real wire format rather than a
    fabricated top-level ``0x43`` header. ``zz`` is the raw 2-bit ZZ field
    (0=not switched, 1=output 1, 2=output 2, 3=invalid).

    Example for FAdr=4, ZZ=10 (output 2)::

        09 00 40 00 43 00 04 02 45

    """
    fadr_ms = (fadr >> 8) & 0xFF
    fadr_ls = fadr & 0xFF
    return build_xbus(0x43, bytes((fadr_ms, fadr_ls, zz & 0x03)))


# --- Receive path: decoded datasets -----------------------------------------


@dataclass(frozen=True)
class SerialNumber:
    """Decoded LAN_GET_SERIAL_NUMBER response (2.1)."""

    serial: int  # 32-bit unsigned


@dataclass(frozen=True)
class HwInfo:
    """Decoded LAN_GET_HWINFO response (2.20).

    ``fw_version`` is kept as the raw 32-bit value (the spec encodes it as BCD);
    presentation is left to the caller.
    """

    hw_type: int  # 32-bit unsigned
    fw_version: int  # 32-bit unsigned


def _decode_serial_number(payload: bytes) -> SerialNumber | None:
    """Decode a serial-number payload; ``None`` if too short to hold one."""
    if len(payload) < 4:
        return None
    (serial,) = struct.unpack_from("<I", payload)
    return SerialNumber(serial=serial)


def _decode_hwinfo(payload: bytes) -> HwInfo | None:
    """Decode a hardware-info payload; ``None`` if too short to hold one."""
    if len(payload) < 8:
        return None
    hw_type, fw_version = struct.unpack_from("<II", payload)
    return HwInfo(hw_type=hw_type, fw_version=fw_version)


@dataclass(frozen=True)
class TurnoutInfo:
    """Decoded LAN_X_TURNOUT_INFO response (5.3).

    ``position`` is 0 (output 1), 1 (output 2), or None (not switched yet / ZZ=00).
    ``invalid`` is True when ZZ=11 (invalid combination).
    """

    fadr: int  # raw function address
    position: int | None  # 0, 1, or None (not switched yet)
    invalid: bool  # True when ZZ=11


def _decode_turnout_info(payload: bytes) -> TurnoutInfo | None:
    """Decode a turnout info payload; ``None`` if too short."""
    if len(payload) < 3:
        return None
    fadr_ms, fadr_ls, db2 = struct.unpack_from("<BBB", payload, 0)
    fadr = (fadr_ms << 8) | fadr_ls
    zz = db2 & 0x03  # bits 0–1: 0=not switched, 1=output 1, 2=output 2, 3=invalid
    if zz == 1:
        position: int | None = 0  # P=0 (output 1)
    elif zz == 2:
        position = 1  # P=1 (output 2)
    else:
        position = None  # ZZ=00 not switched yet, or ZZ=11 invalid
    return TurnoutInfo(fadr=fadr, position=position, invalid=zz == 3)


@dataclass(frozen=True)
class SystemState:
    """Decoded LAN_SYSTEMSTATE_DATACHANGED payload (2.18).

    Electrical telemetry plus the decoded Central State / CentralStateEx flags.
    Raw bitmask ints are retained alongside the decoded booleans so callers can
    inspect bits not surfaced as named booleans.
    """

    # Electrical telemetry
    main_current: int  # mA (INT16)
    prog_current: int  # mA (INT16)
    filtered_main_current: int  # mA (INT16)
    temperature: int  # °C (INT16)
    supply_voltage: int  # mV (UINT16)
    vcc_voltage: int  # mV (UINT16), identical to track voltage

    # Raw bitmasks
    central_state: int
    central_state_ex: int
    capabilities: int

    # Decoded Central State flags
    emergency_stop: bool
    track_voltage_off: bool
    short_circuit: bool
    programming_mode_active: bool

    # Decoded CentralStateEx flags
    high_temperature: bool
    power_lost: bool

    # True only when a nonzero Capabilities byte was present (FW >= 1.42).
    # Older firmware reports 0 / omits the field; capabilities must be ignored.
    capabilities_valid: bool


# Struct for the six little-endian electrical values (offsets 0..11):
# INT16 main, INT16 prog, INT16 filtered-main, INT16 temperature,
# UINT16 supply, UINT16 vcc.
_SYSTEM_STATE_ELECTRICAL = struct.Struct("<hhhhHH")


def _decode_system_state(payload: bytes) -> SystemState | None:
    """Decode a System State payload, tolerating older/truncated firmware data.

    Returns ``None`` for a too-short payload (fewer than the six electrical
    values), so the caller skips it rather than raising.
    """
    if len(payload) < _SYSTEM_STATE_ELECTRICAL.size:  # 12 bytes
        return None

    (
        main_current,
        prog_current,
        filtered_main_current,
        temperature,
        supply_voltage,
        vcc_voltage,
    ) = _SYSTEM_STATE_ELECTRICAL.unpack_from(payload)

    # Bitmask bytes are guarded by length: older/short payloads default to 0.
    central_state = payload[12] if len(payload) >= 13 else 0
    central_state_ex = payload[13] if len(payload) >= 14 else 0
    # payload[14] is reserved. Capabilities lives at offset 15 (FW >= 1.42).
    capabilities = payload[15] if len(payload) >= 16 else 0
    capabilities_valid = len(payload) >= 16 and capabilities != 0

    return SystemState(
        main_current=main_current,
        prog_current=prog_current,
        filtered_main_current=filtered_main_current,
        temperature=temperature,
        supply_voltage=supply_voltage,
        vcc_voltage=vcc_voltage,
        central_state=central_state,
        central_state_ex=central_state_ex,
        capabilities=capabilities,
        emergency_stop=bool(central_state & CentralState.EMERGENCY_STOP),
        track_voltage_off=bool(central_state & CentralState.TRACK_VOLTAGE_OFF),
        short_circuit=bool(central_state & CentralState.SHORT_CIRCUIT),
        programming_mode_active=bool(
            central_state & CentralState.PROGRAMMING_MODE_ACTIVE
        ),
        high_temperature=bool(central_state_ex & CentralStateEx.HIGH_TEMPERATURE),
        power_lost=bool(central_state_ex & CentralStateEx.POWER_LOST),
        capabilities_valid=capabilities_valid,
    )


# X-Header -> (logical header, decoder) for messages tunneled under HDR_X
# (0x40). LAN_X multiplexes many sub-messages by X-Header (turnout info 0x43,
# loco info, BC track power 0x61, ...), so it needs a second-level dispatch on
# the X-Header. Each entry declares the stable logical header the decoded
# dataset is surfaced under, keeping downstream keying (client pending futures,
# coordinator) independent of the 0x40 tunnel. Adding an inbound X-bus message
# later is one new entry here plus its decoder.
_XBUS_DISPATCH = {
    0x43: (HDR_TURNOUT_INFO, _decode_turnout_info),
}


def decode_xbus(payload: bytes) -> tuple[int, object] | None:
    """Decode a LAN_X (0x40) payload into ``(logical_header, dataset)``.

    The payload is ``X-Header | DB.. | XOR-Byte``. Validates the XOR checkbyte,
    strips the X-Header and checkbyte, then sub-dispatches on the X-Header via
    :data:`_XBUS_DISPATCH`. Returns ``None`` for a too-short payload, a bad
    checkbyte, an unknown X-Header, or a sub-decoder that declines — mirroring
    the "never raise, skip the unknown" contract of the top-level dispatch.
    """
    if len(payload) < 2:  # need at least X-Header + XOR
        return None
    checksum = 0
    for byte in payload[:-1]:
        checksum ^= byte
    if checksum != payload[-1]:
        return None
    x_header = payload[0]
    entry = _XBUS_DISPATCH.get(x_header)
    if entry is None:
        return None
    logical_header, decoder = entry
    decoded = decoder(payload[1:-1])  # inner: X-Header and checkbyte stripped
    if decoded is None:
        return None
    return logical_header, decoded


# Header -> decoder. Adding a control-related inbound message later is a new
# entry here plus its decoder (ADR-0001 receive dispatch table). LAN_X (0x40)
# messages are handled separately via decode_xbus (second-level X-Header
# dispatch), not through this top-level table.
_DISPATCH = {
    HDR_SYSTEMSTATE_DATACHANGED: _decode_system_state,
}

# Full receive dispatch for transport clients: the header-keyed table the async
# client decodes and routes on (ADR-0001 receive seam). A superset of _DISPATCH
# so parse_datagram's SystemState-only contract stays unchanged. Adding a
# control-related inbound message later is one new entry here plus its decoder;
# LAN_X (0x40) messages are demultiplexed via decode_xbus instead.
RECEIVE_DISPATCH = {
    HDR_SERIAL_NUMBER: _decode_serial_number,
    HDR_HWINFO: _decode_hwinfo,
    HDR_SYSTEMSTATE_DATACHANGED: _decode_system_state,
}


def split_datasets(data: bytes) -> list[tuple[int, bytes]]:
    """Split a UDP payload into ``(header, payload)`` datasets — framing only.

    The length-driven walk shared by every receive path: steps dataset by
    dataset using each ``DataLen`` and returns the raw ``(Header, Data)`` pairs
    without decoding or dispatching. Malformed framing (``DataLen < 4`` or a
    length overrunning the buffer) stops the walk; a trailing partial byte is
    ignored. Never raises on bad input.
    """
    datasets: list[tuple[int, bytes]] = []
    offset = 0
    total = len(data)

    while offset + 2 <= total:
        data_len = int.from_bytes(data[offset : offset + 2], "little")
        # A dataset is at least the 4 framing bytes; it must not overrun.
        if data_len < 4 or offset + data_len > total:
            break

        header = int.from_bytes(data[offset + 2 : offset + 4], "little")
        payload = data[offset + 4 : offset + data_len]
        datasets.append((header, payload))

        offset += data_len

    return datasets


def parse_datagram(data: bytes) -> list[SystemState | TurnoutInfo]:
    """Split a UDP payload into datasets and decode the known ones.

    Length-driven and total: walks the buffer via :func:`split_datasets`,
    dispatches on ``Header``, and returns every successfully decoded dataset.
    Unknown headers, short/malformed datasets, and older firmware payloads are
    skipped — this never raises on bad input.
    """
    results: list[SystemState | TurnoutInfo] = []
    for header, payload in split_datasets(data):
        if header == HDR_X:
            xbus = decode_xbus(payload)
            if xbus is not None:
                results.append(xbus[1])
            continue
        decoder = _DISPATCH.get(header)
        if decoder is not None:
            decoded = decoder(payload)
            if decoded is not None:
                results.append(decoded)

    return results
