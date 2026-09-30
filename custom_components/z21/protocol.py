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

import logging
import struct
from dataclasses import dataclass
from enum import IntFlag

_LOGGER = logging.getLogger(__name__)

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
# NOTE: 0xEF is the *X-Header* of LAN_X_LOCO_INFO (4.4), likewise carried under
# HDR_X (0x40), not a top-level Header. Kept as the stable logical routing key
# ``decode_xbus`` surfaces loco feedback under (see ``_XBUS_DISPATCH``), so the
# client's pending-future dict and the coordinator can key on it directly.
HDR_LOCO_INFO = 0xEF  # LAN_X_LOCO_INFO X-Header (4.4)

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


# Speed-step mode -> the KKK value the Z21 reports in LAN_X_LOCO_INFO DB2 (4.4);
# the inverse of ``_INFO_KKK_TO_STEPS`` (defined in the loco-drive section).
_STEPS_TO_INFO_KKK = {14: 0x00, 28: 0x02, 128: 0x04}


def build_loco_info(
    address: int,
    *,
    forward: bool,
    step: int,
    speed_steps: int,
    estop: bool = False,
    busy: bool = False,
    functions: int | None = None,
) -> bytes:
    """LAN_X_LOCO_INFO datagram as the Z21 sends it (4.4).

    The inbound counterpart to :func:`build_loco_info_get`, framed under
    ``HDR_X`` with X-Header ``0xEF``. Provided so tests (and any round-trip)
    exercise the real wire format rather than a fabricated header. DB2 is
    ``0000BKKK`` (B = busy, KKK the speed-step code) and DB3 is ``RVVVVVVV``.
    Function bits DB4–DB8 are appended only when ``functions`` (bit n = Fn) is
    given; see :func:`_encode_function_bits`.

    Example — addr 3, DCC 128, forward, step 1::

        0A 00 40 00 EF 00 03 04 82 <xor>

    """
    adr_msb = (address >> 8) & 0x3F
    adr_lsb = address & 0xFF
    db2 = (0x08 if busy else 0x00) | _STEPS_TO_INFO_KKK[speed_steps]
    db3 = (0x80 if forward else 0x00) | encode_speed(step, speed_steps, estop=estop)
    db = bytes((adr_msb, adr_lsb, db2, db3))
    if functions is not None:
        db += _encode_function_bits(functions)
    return build_xbus(HDR_LOCO_INFO, db)


# --- Loco functions (4.3.1, 4.4) ---------------------------------------------


def _encode_function_bits(functions: int) -> bytes:
    """Pack a function bitmask (bit n = Fn) into LAN_X_LOCO_INFO DB4–DB8 (4.4).

    DB4 is ``0DSLFGHJ`` — L = F0, J/H/G/F = F1–F4 (D/S left clear); DB5, DB6,
    DB7 carry F5–F12, F13–F20, F21–F28 with the lowest function in bit 0; DB8
    carries F29–F31 in bits 0–2.
    """
    db4 = ((functions & 0x01) << 4) | ((functions >> 1) & 0x0F)
    return bytes((
        db4,
        (functions >> 5) & 0xFF,
        (functions >> 13) & 0xFF,
        (functions >> 21) & 0xFF,
        (functions >> 29) & 0x07,
    ))


def _decode_function_bits(db: bytes) -> int:
    """Unpack LAN_X_LOCO_INFO DB4.. into a bitmask (bit n = Fn) — see above.

    Tolerates a short tail: absent bytes (e.g. DB8 before FW 1.42) read as off.
    """
    db = db[:5].ljust(5, b"\x00")
    functions = ((db[0] >> 4) & 0x01) | ((db[0] & 0x0F) << 1)
    functions |= db[1] << 5
    functions |= db[2] << 13
    functions |= db[3] << 21
    functions |= (db[4] & 0x07) << 29
    return functions


def build_loco_function(address: int, function: int, *, on: bool) -> bytes:
    """LAN_X_SET_LOCO_FUNCTION (4.3.1): switch one loco function on or off.

    X-Header ``0xE4``, DB0 ``0xF8``, the address packed as in
    :func:`build_loco_drive` (``0xC0 | Adr_MSB`` for addresses ≥ 128), and DB3
    ``TTNNNNNN`` where ``TT`` is the switch type (``00`` off, ``01`` on; the
    ``10`` toggle is not used) and ``NNNNNN`` the function index (0 = F0).

    Example — addr 3, F1 on::

        0A 00 40 00 E4 F8 00 03 41 <xor>

    """
    adr_msb = (address >> 8) & 0x3F
    adr_lsb = address & 0xFF
    db1 = (0xC0 | adr_msb) if address >= 128 else adr_msb
    db3 = (0x40 if on else 0x00) | (function & 0x3F)
    return build_xbus(0xE4, bytes((0xF8, db1, adr_lsb, db3)))


# --- Loco drive: speed coding + builders (4.1, 4.2) --------------------------

# Speed-step mode -> the S nibble of DB0 (``0x10 | S``) in LAN_X_SET_LOCO_DRIVE
# (4.2). S=0: DCC 14, S=2: DCC 28, S=3: DCC 128. KKK in LAN_X_LOCO_INFO (4.4)
# reports the same modes as 0/2/4; both mappings are derived from these three
# canonical step counts.
_DRIVE_S = {14: 0x00, 28: 0x02, 128: 0x03}
# LAN_X_LOCO_INFO DB2 KKK field (4.4): 0=14, 2=28, 4=128.
_INFO_KKK_TO_STEPS = {0: 14, 2: 28, 4: 128}


def max_speed_step(speed_steps: int) -> int:
    """Return the highest drivable step for a 14 / 28 / 128 step mode (4.2).

    128-step mode has 126 drivable steps — its other two codes are Stop and
    E-Stop — while 14 and 28 step modes drive up to their nominal count.
    """
    return 126 if speed_steps == 128 else speed_steps


def rescale_speed_step(step: int, from_steps: int, to_steps: int) -> int:
    """Rescale a raw ``step`` from one 14 / 28 / 128 step mode to another (4.2).

    Proportional over the drivable range (:func:`max_speed_step`), rounded to
    the nearest step and clamped to the target maximum. Stop stays Stop, and a
    moving step never rounds down to Stop — a crawl in a finer mode is step 1
    in a coarser one.
    """
    if step <= 0:
        return 0
    to_max = max_speed_step(to_steps)
    scaled = round(step * to_max / max_speed_step(from_steps))
    return max(1, min(scaled, to_max))


def encode_speed(step: int, speed_steps: int, *, estop: bool = False) -> int:
    """Encode a raw speed ``step`` into the 7-bit ``VVVVVVV`` field of DB3 (4.2).

    The returned value never has the direction bit (0x80) set — the caller ORs
    ``R`` in. ``step`` 0 is a **normal Stop** (``0000000``); ``estop=True`` is the
    distinct **E-Stop** encoding (``0000001``), which takes precedence over the
    step value. The coding mirrors NMRA S 9.2 / S 9.2.1:

    - **14** (S=0): ``000 VVVV`` with ``VVVV = step + 1`` (step 14 -> ``0x0F``).
    - **28** (S=2): the fifth bit ``V5`` carries the split intermediate step —
      ``raw = step + 3``; the low four bits are ``raw >> 1`` and ``V5`` is
      ``raw & 1`` (step 1 -> ``0x02``, step 2 -> ``0x12``, step 28 -> ``0x1F``).
    - **128** (S=3): ``VVVVVVV = step + 1`` (step 126 -> ``0x7F``).
    """
    if estop:
        return 0x01
    if step <= 0:
        return 0x00
    if speed_steps == 28:
        raw = step + 3  # 2..29 map onto the split-V5 layout
        return ((raw & 1) << 4) | ((raw >> 1) & 0x0F)
    # 14 and 128 share the plain "value = step + 1" coding, differing only in
    # width (which the caller's step range already bounds).
    return (step + 1) & 0x7F


def decode_speed(db3: int, speed_steps: int) -> tuple[int, bool]:
    """Decode DB3 ``RVVVVVVV`` into ``(step, estop)`` — the inverse of speed coding.

    The direction bit ``R`` (0x80) is ignored; only the 7-bit speed field is
    read. Returns ``(0, False)`` for Stop and ``(0, True)`` for E-Stop. Mirrors
    :func:`encode_speed` across all three modes (4.2, and 4.4's shared coding).
    """
    v = db3 & 0x7F
    if speed_steps == 28:
        low4 = v & 0x0F
        if low4 == 0:  # V5-independent: ...0 0000 is Stop
            return 0, False
        if low4 == 1:  # ...0 0001 is E-Stop
            return 0, True
        v5 = (v >> 4) & 0x01
        return ((low4 << 1) | v5) - 3, False
    # 14 and 128: plain value = step + 1; 0 = Stop, 1 = E-Stop.
    if v == 0:
        return 0, False
    if v == 1:
        return 0, True
    return v - 1, False


def build_loco_drive(
    address: int,
    *,
    step: int,
    forward: bool,
    speed_steps: int,
    estop: bool = False,
) -> bytes:
    """LAN_X_SET_LOCO_DRIVE (4.2): set a loco's coupled speed **and** direction.

    X-Header ``0xE4``, DB0 ``0x10 | S`` (S from ``speed_steps``), the loco
    address packed as ``Adr_MSB = (address >> 8) & 0x3F`` / ``Adr_LSB``, and DB3
    ``RVVVVVVV`` where ``R`` is the direction (1 = forward) and ``VVVVVVV`` is
    :func:`encode_speed`. Addresses ≥ 128 set the two high bits of DB1
    (``DB1 = 0xC0 | Adr_MSB``, spec 4.2); below 128 those bits are meaningless
    but the command still works, so they are left clear.

    ``step`` 0 is a normal Stop; ``estop=True`` emits the distinct E-Stop code.
    Both preserve ``forward`` so a halt does not silently flip direction.

    Example — addr 3, DCC 128, forward, step 1::

        0A 00 40 00 E4 13 00 03 82 76

    """
    db0 = 0x10 | _DRIVE_S[speed_steps]
    adr_msb = (address >> 8) & 0x3F
    adr_lsb = address & 0xFF
    db1 = (0xC0 | adr_msb) if address >= 128 else adr_msb
    r_bit = 0x80 if forward else 0x00
    db3 = r_bit | encode_speed(step, speed_steps, estop=estop)
    return build_xbus(0xE4, bytes((db0, db1, adr_lsb, db3)))


def build_loco_info_get(address: int) -> bytes:
    """LAN_X_GET_LOCO_INFO request (4.1): poll **and** subscribe a loco.

    X-Header ``0xE3``, DB0 ``0xF0``, address packed as in :func:`build_loco_drive`
    (the ``0xC0 | Adr_MSB`` rule for addresses ≥ 128). Sending this both returns
    the current LAN_X_LOCO_INFO and subscribes the client to future changes for
    this address (in combination with the driving/switching broadcast flag).

    Example — addr 3::

        09 00 40 00 E3 F0 00 03 10

    """
    adr_msb = (address >> 8) & 0x3F
    adr_lsb = address & 0xFF
    db1 = (0xC0 | adr_msb) if address >= 128 else adr_msb
    return build_xbus(0xE3, bytes((0xF0, db1, adr_lsb)))


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
class LocoInfo:
    """Decoded LAN_X_LOCO_INFO response (4.4).

    ``speed`` is the raw DCC step (0 = Stop); ``estop`` distinguishes an
    immediate emergency stop from a normal step-0 stop. ``speed_steps`` is the
    mode the Z21 reports (14 / 28 / 128) and ``busy`` is True when the loco is
    being driven by another X-BUS handset. ``functions`` is the F0–F31 state
    as a bitmask (bit n = Fn), or ``None`` when the datagram carried no
    function bytes (DB4..).
    """

    address: int  # DCC loco address
    forward: bool  # direction: True = forward (R bit)
    speed: int  # raw speed step, 0 = Stop
    estop: bool  # True = immediate emergency stop
    speed_steps: int  # reported mode: 14, 28, or 128
    busy: bool  # controlled by another handset
    functions: int | None = None  # bit n = Fn on; None if not reported


def _decode_loco_info(payload: bytes) -> LocoInfo | None:
    """Decode a loco-info payload (DB0..DB3, optional DB4..DB8); ``None`` if short.

    Reads the drive fields: address (DB0/DB1, high bits of Adr_MSB ignored
    per 4.4), the busy bit and speed-step code from DB2 ``0000BKKK``, and
    direction/speed from DB3 ``RVVVVVVV`` via :func:`decode_speed`. An unknown
    KKK defaults to 128-step decoding rather than raising. Function bits are
    decoded from DB4 onward when present.
    """
    if len(payload) < 4:  # need DB0..DB3
        return None
    adr_msb, adr_lsb, db2, db3 = struct.unpack_from("<BBBB", payload, 0)
    address = ((adr_msb & 0x3F) << 8) | adr_lsb
    busy = bool(db2 & 0x08)
    speed_steps = _INFO_KKK_TO_STEPS.get(db2 & 0x07, 128)
    forward = bool(db3 & 0x80)
    speed, estop = decode_speed(db3, speed_steps)
    return LocoInfo(
        address=address,
        forward=forward,
        speed=speed,
        estop=estop,
        speed_steps=speed_steps,
        busy=busy,
        functions=_decode_function_bits(payload[4:]) if len(payload) > 4 else None,
    )


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
    0xEF: (HDR_LOCO_INFO, _decode_loco_info),
}


def decode_xbus(payload: bytes) -> tuple[int, object] | None:
    """Decode a LAN_X (0x40) payload into ``(logical_header, dataset)``.

    The payload is ``X-Header | DB.. | XOR-Byte``. Sub-dispatches on the
    X-Header via :data:`_XBUS_DISPATCH` after stripping the X-Header and
    checkbyte. Returns ``None`` for a too-short payload, an unknown X-Header, or
    a sub-decoder that declines — mirroring the "never raise, skip the unknown"
    contract of the top-level dispatch.

    The trailing XOR checkbyte is treated as **advisory**, not gating: real Z21
    firmware sends ``LAN_X_TURNOUT_INFO`` (5.3) with a checkbyte that does not
    match the spec's "XOR of X-Header and data bytes" rule (observed on FW
    1.42 / HW 0x201 — e.g. ``09 00 40 00 43 00 64 02 6c`` where that XOR is
    ``0x25``, not ``0x6c``). Because the LAN length prefix and UDP datagram
    boundaries already delimit the message, the XOR adds no framing safety here;
    dropping on mismatch silently discarded every turnout position update. We
    therefore log a mismatch at debug level and decode anyway.
    """
    if len(payload) < 2:  # need at least X-Header + XOR
        return None
    checksum = 0
    for byte in payload[:-1]:
        checksum ^= byte
    if checksum != payload[-1]:
        _LOGGER.debug(
            "LAN_X checkbyte mismatch (computed 0x%02x, wire 0x%02x) for %s; "
            "decoding anyway",
            checksum,
            payload[-1],
            payload.hex(" "),
        )
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


def parse_datagram(data: bytes) -> list[SystemState | TurnoutInfo | LocoInfo]:
    """Split a UDP payload into datasets and decode the known ones.

    Length-driven and total: walks the buffer via :func:`split_datasets`,
    dispatches on ``Header``, and returns every successfully decoded dataset.
    Unknown headers, short/malformed datasets, and older firmware payloads are
    skipped — this never raises on bad input.
    """
    results: list[SystemState | TurnoutInfo | LocoInfo] = []
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
