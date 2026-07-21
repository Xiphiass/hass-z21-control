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

# --- Broadcast flags (2.16) -------------------------------------------------

# The System State broadcast group: delivers LAN_SYSTEMSTATE_DATACHANGED.
# NOTE: 0x00000001 is the *driving & switching* group, NOT system state — a
# common mix-up. v1 subscribes only to system state.
BROADCAST_FLAG_SYSTEM_STATE = 0x00000100


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


# Header -> decoder. Adding a control-related inbound message later is a new
# entry here plus its decoder (ADR-0001 receive dispatch table).
_DISPATCH = {
    HDR_SYSTEMSTATE_DATACHANGED: _decode_system_state,
}

# Full receive dispatch for transport clients: the header-keyed table the async
# client decodes and routes on (ADR-0001 receive seam). A superset of _DISPATCH
# so parse_datagram's SystemState-only contract stays unchanged. Adding a
# control-related inbound message later is one new entry here plus its decoder.
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


def parse_datagram(data: bytes) -> list[SystemState]:
    """Split a UDP payload into datasets and decode the known ones.

    Length-driven and total: walks the buffer via :func:`split_datasets`,
    dispatches on ``Header``, and returns every successfully decoded dataset.
    Unknown headers, short/malformed datasets, and older firmware payloads are
    skipped — this never raises on bad input.
    """
    results: list[SystemState] = []
    for header, payload in split_datasets(data):
        decoder = _DISPATCH.get(header)
        if decoder is not None:
            decoded = decoder(payload)
            if decoded is not None:
                results.append(decoded)

    return results
