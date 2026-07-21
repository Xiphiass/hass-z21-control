"""Seam-1 protocol-compliance suite for the pure Z21 codec.

Verifies exact outbound bytes against the spec's hex examples, System State
decoding of electrical values and every Central State / CentralStateEx flag,
combined-datagram splitting, and graceful handling of unknown/short/malformed
and older-firmware datasets. Also guards the HA-free / socket-free seam.
"""

from __future__ import annotations

import struct
from pathlib import Path

from custom_components.z21 import protocol
from custom_components.z21.protocol import (
    BROADCAST_FLAG_SYSTEM_STATE,
    HDR_SYSTEMSTATE_DATACHANGED,
    CentralState,
    CentralStateEx,
    SystemState,
    build_frame,
    build_get_hwinfo,
    build_get_serial_number,
    build_logoff,
    build_set_broadcastflags,
    build_set_stop,
    build_systemstate_getdata,
    build_track_power_off,
    build_track_power_on,
    build_xbus,
    parse_datagram,
)


# --- Outbound builders: exact bytes -----------------------------------------


def test_get_serial_number_exact_bytes():
    assert build_get_serial_number() == bytes.fromhex("04001000")


def test_get_hwinfo_exact_bytes():
    assert build_get_hwinfo() == bytes.fromhex("04001a00")


def test_logoff_exact_bytes():
    assert build_logoff() == bytes.fromhex("04003000")


def test_systemstate_getdata_exact_bytes():
    assert build_systemstate_getdata() == bytes.fromhex("04008500")


def test_set_broadcastflags_default_exact_bytes():
    # DataLen=0x0008, Header=0x0050, flags=0x00000100 (LE32) -> system state.
    assert build_set_broadcastflags() == bytes.fromhex("0800500000010000")


def test_set_broadcastflags_default_flag_is_system_state():
    assert BROADCAST_FLAG_SYSTEM_STATE == 0x00000100


def test_set_broadcastflags_custom_flags():
    assert build_set_broadcastflags(0x00000001) == bytes.fromhex("0800500001000000")


def test_build_frame_prepends_len_and_header():
    frame = build_frame(0x84, b"\xaa\xbb")
    # DataLen = 2 payload + 4 framing = 6.
    assert frame == bytes.fromhex("06008400") + b"\xaa\xbb"


# --- X-bus control builders --------------------------------------------------


def test_track_power_off_exact_bytes():
    # DataLen=0x0007, Header=0x0040, X-Header=0x21, DB0=0x80, XOR=0xA1.
    assert build_track_power_off() == bytes.fromhex("0700400021 80 a1".replace(" ", ""))


def test_track_power_on_exact_bytes():
    # DataLen=0x0007, Header=0x0040, X-Header=0x21, DB0=0x81, XOR=0xA0.
    assert build_track_power_on() == bytes.fromhex("0700400021 81 a0".replace(" ", ""))


def test_set_stop_exact_bytes():
    # DataLen=0x0006, Header=0x0040, X-Header=0x80, XOR=0x80 (no DB0).
    assert build_set_stop() == bytes.fromhex("060040008080")


def test_build_xbus_computes_xor_checkbyte():
    # XOR over X-header 0x21 and DB0 0x80 -> 0xA1.
    frame = build_xbus(0x21, b"\x80")
    assert frame[-1] == 0x21 ^ 0x80
    assert frame == build_frame(protocol.HDR_X, b"\x21\x80\xa1")


# --- System State decoding ---------------------------------------------------


def _system_state_datagram(
    main=0,
    prog=0,
    filtered=0,
    temp=0,
    supply=0,
    vcc=0,
    central=0,
    central_ex=0,
    reserved=0,
    capabilities=0,
    *,
    payload_len=16,
):
    """Build a LAN_SYSTEMSTATE_DATACHANGED datagram with a chosen payload length."""
    payload = struct.pack("<hhhhHH", main, prog, filtered, temp, supply, vcc)
    payload += bytes([central, central_ex, reserved, capabilities])
    payload = payload[:payload_len]
    return build_frame(HDR_SYSTEMSTATE_DATACHANGED, payload)


def test_system_state_electrical_values():
    # Negative currents/temperature exercise the signed INT16 decode.
    dgram = _system_state_datagram(
        main=-100, prog=5, filtered=250, temp=-3, supply=15000, vcc=16500
    )
    (state,) = parse_datagram(dgram)
    assert isinstance(state, SystemState)
    assert state.main_current == -100
    assert state.prog_current == 5
    assert state.filtered_main_current == 250
    assert state.temperature == -3
    assert state.supply_voltage == 15000
    assert state.vcc_voltage == 16500


def test_system_state_all_flags_set():
    central = (
        CentralState.EMERGENCY_STOP
        | CentralState.TRACK_VOLTAGE_OFF
        | CentralState.SHORT_CIRCUIT
        | CentralState.PROGRAMMING_MODE_ACTIVE
    )
    central_ex = (
        CentralStateEx.HIGH_TEMPERATURE
        | CentralStateEx.POWER_LOST
        | CentralStateEx.SHORT_CIRCUIT_EXTERNAL
        | CentralStateEx.SHORT_CIRCUIT_INTERNAL
        | CentralStateEx.RCN213
    )
    dgram = _system_state_datagram(
        central=int(central), central_ex=int(central_ex), capabilities=0x01
    )
    (state,) = parse_datagram(dgram)

    assert state.central_state == int(central)
    assert state.central_state_ex == int(central_ex)
    assert state.emergency_stop is True
    assert state.track_voltage_off is True
    assert state.short_circuit is True
    assert state.programming_mode_active is True
    assert state.high_temperature is True
    assert state.power_lost is True
    assert state.capabilities == 0x01
    assert state.capabilities_valid is True


def test_system_state_no_flags_set():
    (state,) = parse_datagram(_system_state_datagram(capabilities=0x01))
    assert state.emergency_stop is False
    assert state.track_voltage_off is False
    assert state.short_circuit is False
    assert state.programming_mode_active is False
    assert state.high_temperature is False
    assert state.power_lost is False


# --- Combined datagram -------------------------------------------------------


def test_combined_datagram_parsed_independently():
    first = _system_state_datagram(main=111, central=int(CentralState.SHORT_CIRCUIT))
    second = _system_state_datagram(main=222, temp=40)
    states = parse_datagram(first + second)
    assert len(states) == 2
    assert states[0].main_current == 111
    assert states[0].short_circuit is True
    assert states[1].main_current == 222
    assert states[1].temperature == 40


def test_combined_datagram_with_unknown_and_valid():
    # An unknown-header dataset sandwiched between two valid ones is skipped.
    unknown = build_frame(0x40, b"\x01\x02\x03")
    dgram = (
        _system_state_datagram(main=1)
        + unknown
        + _system_state_datagram(main=2)
    )
    states = parse_datagram(dgram)
    assert [s.main_current for s in states] == [1, 2]


# --- Robustness: never raise -------------------------------------------------


def test_empty_input():
    assert parse_datagram(b"") == []


def test_unknown_header_ignored():
    assert parse_datagram(build_frame(0x99, b"\x00\x00")) == []


def test_datalen_overrunning_buffer_skipped():
    # DataLen says 20 bytes but only a few follow.
    dgram = struct.pack("<HH", 0x14, HDR_SYSTEMSTATE_DATACHANGED) + b"\x00\x00"
    assert parse_datagram(dgram) == []


def test_datalen_too_small_skipped():
    # DataLen < 4 is malformed framing.
    assert parse_datagram(struct.pack("<HH", 0x02, HDR_SYSTEMSTATE_DATACHANGED)) == []


def test_trailing_odd_byte_ignored():
    valid = _system_state_datagram(main=7)
    states = parse_datagram(valid + b"\x01")
    assert len(states) == 1
    assert states[0].main_current == 7


def test_truncated_system_state_skipped():
    # Only 8 payload bytes: fewer than the six electrical values (12).
    dgram = _system_state_datagram(payload_len=8)
    assert parse_datagram(dgram) == []


def test_older_firmware_without_capabilities():
    # 14-byte payload: electrical + both bitmasks, no reserved/Capabilities byte.
    dgram = _system_state_datagram(
        central=int(CentralState.TRACK_VOLTAGE_OFF), payload_len=14
    )
    (state,) = parse_datagram(dgram)
    assert state.track_voltage_off is True
    assert state.capabilities == 0
    assert state.capabilities_valid is False


def test_capabilities_zero_is_invalid():
    # Full 16-byte payload but Capabilities == 0 -> older firmware, ignore it.
    (state,) = parse_datagram(_system_state_datagram(capabilities=0))
    assert state.capabilities == 0
    assert state.capabilities_valid is False


def test_partial_bitmask_only_central_state():
    # 13-byte payload: electrical + CentralState only, no CentralStateEx.
    dgram = _system_state_datagram(
        central=int(CentralState.EMERGENCY_STOP), payload_len=13
    )
    (state,) = parse_datagram(dgram)
    assert state.emergency_stop is True
    assert state.central_state_ex == 0
    assert state.capabilities_valid is False


# --- Seam guard: no HA / socket / asyncio imports ---------------------------


def test_codec_has_no_forbidden_imports():
    src = Path(protocol.__file__).read_text()
    for forbidden in ("import asyncio", "import socket", "homeassistant"):
        assert forbidden not in src, f"protocol.py must not reference {forbidden!r}"
