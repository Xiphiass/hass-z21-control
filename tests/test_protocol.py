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
    HDR_LOCO_INFO,
    HDR_SYSTEMSTATE_DATACHANGED,
    HDR_TURNOUT_INFO,
    CentralState,
    CentralStateEx,
    LocoInfo,
    SystemState,
    TurnoutInfo,
    build_frame,
    build_get_hwinfo,
    build_get_serial_number,
    build_loco_drive,
    build_loco_info,
    build_loco_info_get,
    build_logoff,
    build_set_broadcastflags,
    build_set_stop,
    build_systemstate_getdata,
    build_track_power_off,
    build_track_power_on,
    build_turnout_info,
    build_turnout_info_get,
    build_turnout_set,
    build_xbus,
    decode_speed,
    decode_xbus,
    encode_speed,
    parse_datagram,
    _decode_loco_info,
    _decode_turnout_info,
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


def test_turnout_info_get_fadr_4_exact_bytes():
    assert build_turnout_info_get(4) == bytes.fromhex("0800400043000447")


def test_turnout_info_get_fadr_0_exact_bytes():
    assert build_turnout_info_get(0) == bytes.fromhex("0800400043000043")


def test_turnout_info_get_fadr_65534_exact_bytes():
    assert build_turnout_info_get(65534) == bytes.fromhex("0800400043FFFE42")


# DB2 is 10Q0A00P; the integration always uses the queue (Q=1, bit5). A and P
# are independent: A activates/deactivates, P selects output 1 (0) / output 2 (1).


def test_turnout_set_output2_activate_exact_bytes():
    # FAdr=4, output=1, activate, Q=1 -> DB2=0xA9, XOR(0x53,0x00,0x04,0xA9)=0xFE
    assert build_turnout_set(4, 1, activate=True) == bytes.fromhex(
        "09004000530004A9FE"
    )


def test_turnout_set_output2_deactivate_exact_bytes():
    # FAdr=4, output=1, deactivate, Q=1 -> DB2=0xA1, XOR(0x53,0x00,0x04,0xA1)=0xF6
    assert build_turnout_set(4, 1, activate=False) == bytes.fromhex(
        "09004000530004A1F6"
    )


def test_turnout_set_output1_activate_exact_bytes():
    # FAdr=4, output=0, activate, Q=1 -> DB2=0xA8, XOR(0x53,0x00,0x04,0xA8)=0xFF
    assert build_turnout_set(4, 0, activate=True) == bytes.fromhex(
        "09004000530004A8FF"
    )


def test_turnout_set_output1_deactivate_exact_bytes():
    # FAdr=4, output=0, deactivate, Q=1 -> DB2=0xA0, XOR(0x53,0x00,0x04,0xA0)=0xF7
    assert build_turnout_set(4, 0, activate=False) == bytes.fromhex(
        "09004000530004A0F7"
    )


def test_turnout_set_q0_clears_queue_bit():
    # Q=0 -> DB2=0x88, XOR(0x53,0x00,0x04,0x88)=0xDF
    assert build_turnout_set(4, 0, activate=True, q=False) == bytes.fromhex(
        "0900400053000488DF"
    )


def test_turnout_set_fadr_0_output1_activate_exact_bytes():
    # FAdr=0, output=0, activate, Q=1 -> DB2=0xA8, XOR(0x53,0x00,0x00,0xA8)=0xFB
    assert build_turnout_set(0, 0, activate=True) == bytes.fromhex(
        "09004000530000A8FB"
    )


# --- Turnout Info decoding ---------------------------------------------------


# DB2 is 000000ZZ; ZZ lives in bits 0–1 (spec 5.3).


def test_decode_turnout_info_fadr_4_position_1():
    # ZZ=10 (output 2) → byte = 0x02
    payload = struct.pack("<BBB", 0x00, 0x04, 0x02)
    info = _decode_turnout_info(payload)
    assert info is not None
    assert info.fadr == 4
    assert info.position == 1
    assert info.invalid is False


def test_decode_turnout_info_fadr_4_position_0():
    # ZZ=01 (output 1) → byte = 0x01
    payload = struct.pack("<BBB", 0x00, 0x04, 0x01)
    info = _decode_turnout_info(payload)
    assert info is not None
    assert info.fadr == 4
    assert info.position == 0
    assert info.invalid is False


def test_decode_turnout_info_not_switched_yet():
    # ZZ=00 (not switched yet) → byte = 0x00
    payload = struct.pack("<BBB", 0x00, 0x04, 0x00)
    info = _decode_turnout_info(payload)
    assert info is not None
    assert info.fadr == 4
    assert info.position is None
    assert info.invalid is False


def test_decode_turnout_info_invalid():
    # ZZ=11 (invalid) → byte = 0x03
    payload = struct.pack("<BBB", 0x00, 0x04, 0x03)
    info = _decode_turnout_info(payload)
    assert info is not None
    assert info.fadr == 4
    assert info.position is None
    assert info.invalid is True


def test_decode_turnout_info_ignores_high_bits():
    # Only bits 0–1 matter; high bits set must not change ZZ=10 → output 2.
    payload = struct.pack("<BBB", 0x00, 0x04, 0xFE)
    info = _decode_turnout_info(payload)
    assert info is not None
    assert info.position == 1
    assert info.invalid is False


def test_decode_turnout_info_short_payload():
    assert _decode_turnout_info(b"") is None
    assert _decode_turnout_info(b"\x00\x04") is None


def test_decode_turnout_info_fadr_65534():
    payload = struct.pack("<BBB", 0xFF, 0xFE, 0x02)
    info = _decode_turnout_info(payload)
    assert info is not None
    assert info.fadr == 65534
    assert info.position == 1
    assert info.invalid is False


# --- Combined datagram -------------------------------------------------------


def test_combined_datagram_with_turnout_info():
    first = _system_state_datagram(main=1, central=int(CentralState.SHORT_CIRCUIT))
    turnout_dgram = build_turnout_info(4, 0x02)  # real wire framing (5.3)
    second = _system_state_datagram(main=2)
    dgram = first + turnout_dgram + second
    states = parse_datagram(dgram)
    assert len(states) == 3  # SystemState, TurnoutInfo, SystemState
    assert isinstance(states[1], TurnoutInfo)
    assert states[1].fadr == 4
    assert states[1].position == 1


# --- X-bus demux (decode_xbus) ----------------------------------------------


def test_build_turnout_info_exact_bytes():
    # Spec 5.3 example: FAdr=4, ZZ=10 (output 2) -> 09 00 40 00 43 00 04 02 45.
    assert build_turnout_info(4, 0x02) == bytes.fromhex("090040004300040245")


def test_decode_xbus_turnout_info():
    # Strip DataLen+Header framing; decode_xbus sees the X-bus payload.
    _, payload = protocol.split_datasets(build_turnout_info(4, 0x02))[0]
    result = decode_xbus(payload)
    assert result is not None
    header, decoded = result
    assert header == HDR_TURNOUT_INFO
    assert isinstance(decoded, TurnoutInfo)
    assert decoded.fadr == 4
    assert decoded.position == 1


def test_decode_xbus_unknown_x_header():
    # X-Header 0x61 (BC track power) is not in the dispatch table -> ignored.
    payload = build_xbus(0x61, b"\x00")[4:]  # drop DataLen+Header framing
    assert decode_xbus(payload) is None


def test_decode_xbus_checkbyte_is_advisory():
    """A mismatched XOR checkbyte is logged, not gated — the message still decodes.

    Real Z21 firmware sends LAN_X_TURNOUT_INFO (5.3) with a checkbyte that does
    not follow the spec's X-Header^data XOR rule (captured on FW 1.42 / HW 0x201:
    ``09 00 40 00 43 00 64 02 6c``). Dropping on mismatch silently discarded
    every turnout position update, so the checkbyte is treated as advisory. See
    ``decode_xbus``.
    """
    payload = bytearray(build_turnout_info(4, 0x02)[4:])
    payload[-1] ^= 0xFF  # corrupt the XOR checkbyte
    result = decode_xbus(bytes(payload))
    assert result is not None
    header, decoded = result
    assert header == HDR_TURNOUT_INFO
    assert decoded.fadr == 4
    assert decoded.position == 1


def test_decode_xbus_real_turnout_info_frame():
    """The exact bytes a real Z21 sends for a turnout position decode correctly.

    Regression for the checkbyte-gating bug: this frame's spec XOR is 0x25 but
    the wire checkbyte is 0x6c, which the old strict validation rejected.
    """
    # 09 00 40 00 43 00 64 02 6c -> FAdr 100, ZZ=10 (output 2 -> position 1).
    payload = bytes.fromhex("4300640 2 6c".replace(" ", ""))
    result = decode_xbus(payload)
    assert result is not None
    header, decoded = result
    assert header == HDR_TURNOUT_INFO
    assert decoded.fadr == 100
    assert decoded.position == 1
    assert decoded.invalid is False


def test_decode_xbus_too_short():
    assert decode_xbus(b"") is None
    assert decode_xbus(b"\x43") is None


# --- Robustness: never raise -------------------------------------------------


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
    # An unknown top-level header sandwiched between two valid ones is skipped.
    unknown = build_frame(0x99, b"\x01\x02\x03")
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


# --- Loco speed coding (§4.2) ------------------------------------------------


# The three DCC speed-step modes and their step counts (0 = Stop for each).
_MODE_14 = 14
_MODE_28 = 28
_MODE_128 = 128


def test_encode_speed_dcc14_stop_and_estop():
    # Stop is the all-zero speed field; E-Stop is the distinct ...0000001.
    assert encode_speed(0, _MODE_14) == 0x00
    assert encode_speed(0, _MODE_14, estop=True) == 0x01


def test_encode_speed_dcc14_table():
    # §4.2 "DCC 14": step n -> R000 VVVV with VVVV = n + 1 (step 14 = 0x0F max).
    assert encode_speed(1, _MODE_14) == 0x02
    assert encode_speed(2, _MODE_14) == 0x03
    assert encode_speed(13, _MODE_14) == 0x0E
    assert encode_speed(14, _MODE_14) == 0x0F


def test_encode_speed_dcc28_table_split_v5():
    # §4.2 "DCC 28": the fifth bit V5 is the split intermediate step.
    assert encode_speed(0, _MODE_28) == 0x00  # Stop
    assert encode_speed(0, _MODE_28, estop=True) == 0x01  # E-Stop
    assert encode_speed(1, _MODE_28) == 0x02
    assert encode_speed(2, _MODE_28) == 0x12  # V5 set
    assert encode_speed(3, _MODE_28) == 0x03
    assert encode_speed(4, _MODE_28) == 0x13
    assert encode_speed(27, _MODE_28) == 0x0F
    assert encode_speed(28, _MODE_28) == 0x1F  # max


def test_encode_speed_dcc128_table():
    # §4.2 "DCC 128": value = step + 1 (step 126 = 0x7F max).
    assert encode_speed(0, _MODE_128) == 0x00  # Stop
    assert encode_speed(0, _MODE_128, estop=True) == 0x01  # E-Stop
    assert encode_speed(1, _MODE_128) == 0x02
    assert encode_speed(125, _MODE_128) == 0x7E
    assert encode_speed(126, _MODE_128) == 0x7F


def test_encode_speed_never_sets_direction_bit():
    # encode_speed produces only the 7-bit VVVVVVV field; R lives in the builder.
    for mode in (_MODE_14, _MODE_28, _MODE_128):
        for step in range(0, mode - 1):
            assert encode_speed(step, mode) & 0x80 == 0


def test_encode_speed_roundtrip_all_modes():
    for mode in (_MODE_14, _MODE_28, _MODE_128):
        assert decode_speed(encode_speed(0, mode), mode) == (0, False)
        assert decode_speed(encode_speed(0, mode, estop=True), mode) == (0, True)
        for step in range(1, mode - 1):
            assert decode_speed(encode_speed(step, mode), mode) == (step, False)


def test_decode_speed_ignores_direction_bit():
    # The R bit (0x80) must not perturb the decoded step for any mode.
    for mode in (_MODE_14, _MODE_28, _MODE_128):
        raw = encode_speed(5 if mode != _MODE_14 else 3, mode)
        step, estop = decode_speed(raw | 0x80, mode)
        assert estop is False
        assert step == (5 if mode != _MODE_14 else 3)


# --- Loco drive builder (§4.2) -----------------------------------------------


def test_build_loco_drive_dcc128_forward_step1_addr3():
    # Addr 3 (<128): DB1 = Adr_MSB = 0x00, DB2 = 0x03. S=3 -> DB0 = 0x13.
    # DB3 = R(1) VVVVVVV(step1=0x02) = 0x82. XOR(E4,13,00,03,82)=0x76.
    assert build_loco_drive(3, step=1, forward=True, speed_steps=128) == bytes.fromhex(
        "0A0040 00 E4 13 00 03 82 76".replace(" ", "")
    )


def test_build_loco_drive_dcc128_reverse_step1_addr3():
    # DB3 = R(0) 0x02 = 0x02. XOR(E4,13,00,03,02)=0xF6.
    assert build_loco_drive(3, step=1, forward=False, speed_steps=128) == bytes.fromhex(
        "0A004000E4130003 02 F6".replace(" ", "")
    )


def test_build_loco_drive_normal_stop_preserves_direction():
    # Step 0 forward -> DB3 = 0x80 (R set, speed 0).
    frame = build_loco_drive(3, step=0, forward=True, speed_steps=128)
    assert frame[8] == 0x80  # DB3
    # reverse stop -> DB3 = 0x00
    frame_rev = build_loco_drive(3, step=0, forward=False, speed_steps=128)
    assert frame_rev[8] == 0x00


def test_build_loco_drive_estop_is_distinct_encoding():
    # E-Stop forward -> DB3 = R(1) | 0x01 = 0x81, not 0x80 (normal stop).
    frame = build_loco_drive(3, step=0, forward=True, speed_steps=128, estop=True)
    assert frame[8] == 0x81
    frame_rev = build_loco_drive(3, step=0, forward=False, speed_steps=128, estop=True)
    assert frame_rev[8] == 0x01


def test_build_loco_drive_step_modes_set_db0():
    # DB0 = 0x10 | S; S = 0/2/3 for 14/28/128.
    assert build_loco_drive(3, step=1, forward=True, speed_steps=14)[5] == 0x10
    assert build_loco_drive(3, step=1, forward=True, speed_steps=28)[5] == 0x12
    assert build_loco_drive(3, step=1, forward=True, speed_steps=128)[5] == 0x13


def test_build_loco_drive_address_ge_128_sets_high_bits():
    # Addr 128: Adr_MSB = 0, Adr_LSB = 128 -> DB1 = 0xC0 | 0x00 = 0xC0.
    frame = build_loco_drive(128, step=1, forward=True, speed_steps=128)
    assert frame[6] == 0xC0  # DB1
    assert frame[7] == 0x80  # DB2 = Adr_LSB


def test_build_loco_drive_large_address_packs_msb():
    # Addr 1000 = 0x03E8: Adr_MSB = 0x03, Adr_LSB = 0xE8 -> DB1 = 0xC0|0x03 = 0xC3.
    frame = build_loco_drive(1000, step=1, forward=True, speed_steps=128)
    assert frame[6] == 0xC3
    assert frame[7] == 0xE8


def test_build_loco_drive_address_lt_128_leaves_high_bits_clear():
    frame = build_loco_drive(3, step=1, forward=True, speed_steps=128)
    assert frame[6] == 0x00  # DB1 = Adr_MSB, high bits not forced


def test_build_loco_drive_dcc14_max_reverse():
    # 14-step max (step 14), reverse: DB0=0x10, DB3 = 0x0F. XOR(E4,10,00,03,0F)=0xF8
    assert build_loco_drive(3, step=14, forward=False, speed_steps=14) == bytes.fromhex(
        "0A004000E4100003 0F F8".replace(" ", "")
    )


# --- Loco info/subscribe builder (§4.1) --------------------------------------


def test_build_loco_info_get_addr3_exact_bytes():
    # X-Header 0xE3, DB0 0xF0, DB1=Adr_MSB=0x00, DB2=Adr_LSB=0x03.
    # XOR(E3,F0,00,03) = 0x10. DataLen 0x09.
    assert build_loco_info_get(3) == bytes.fromhex("09004000E3F0000310")


def test_build_loco_info_get_address_ge_128():
    # Addr 200 = 0x00C8: Adr_MSB=0, Adr_LSB=0xC8, DB1 = 0xC0.
    frame = build_loco_info_get(200)
    assert frame[4] == 0xE3
    assert frame[5] == 0xF0
    assert frame[6] == 0xC0  # DB1 high bits forced
    assert frame[7] == 0xC8  # DB2 = Adr_LSB


# --- Loco info decoding (§4.4) -----------------------------------------------


def test_decode_loco_info_from_real_frame():
    # DB0=Adr_MSB, DB1=Adr_LSB (addr 3), DB2=0x04 (KKK=4 -> 128 steps, not busy),
    # DB3 = R(1) | step-1 encoding (step 1 -> 0x02) = 0x82.
    payload = bytes((0x00, 0x03, 0x04, 0x82))
    info = _decode_loco_info(payload)
    assert info is not None
    assert info.address == 3
    assert info.forward is True
    assert info.speed == 1
    assert info.estop is False
    assert info.speed_steps == 128
    assert info.busy is False


def test_decode_loco_info_busy_and_reverse():
    # DB2 = 0x08 -> B bit set (busy), KKK=0 (14 steps). DB3 = 0x0F reverse step14.
    payload = bytes((0x00, 0x03, 0x08, 0x0F))
    info = _decode_loco_info(payload)
    assert info is not None
    assert info.busy is True
    assert info.speed_steps == 14
    assert info.forward is False
    assert info.speed == 14
    assert info.estop is False


def test_decode_loco_info_estop():
    # DB3 = R(1) | E-Stop(1) = 0x81 -> estop True, speed 0.
    payload = bytes((0x00, 0x03, 0x04, 0x81))
    info = _decode_loco_info(payload)
    assert info is not None
    assert info.estop is True
    assert info.speed == 0
    assert info.forward is True


def test_decode_loco_info_ignores_adr_msb_high_bits():
    # The two highest bits of Adr_MSB must be ignored per §4.4.
    payload = bytes((0xC3, 0xE8, 0x04, 0x82))  # 0xC3 & 0x3F = 0x03
    info = _decode_loco_info(payload)
    assert info is not None
    assert info.address == 1000


def test_decode_loco_info_28_step_split_v5():
    # KKK=2 -> 28 steps. DB3 = 0x12 -> step 2 (V5 set), forward.
    payload = bytes((0x00, 0x03, 0x02, 0x92))  # R set (0x80) | 0x12
    info = _decode_loco_info(payload)
    assert info is not None
    assert info.speed_steps == 28
    assert info.speed == 2
    assert info.forward is True


def test_decode_loco_info_short_payload():
    assert _decode_loco_info(b"") is None
    assert _decode_loco_info(b"\x00\x03\x04") is None  # need DB0..DB3


def test_build_loco_info_exact_bytes_roundtrips_decode():
    # build_loco_info frames a §4.4 datagram; decode_xbus recovers the dataset.
    frame = build_loco_info(3, forward=True, step=1, speed_steps=128)
    _, payload = protocol.split_datasets(frame)[0]
    result = decode_xbus(payload)
    assert result is not None
    header, decoded = result
    assert header == HDR_LOCO_INFO
    assert isinstance(decoded, LocoInfo)
    assert decoded.address == 3
    assert decoded.speed == 1
    assert decoded.forward is True
    assert decoded.speed_steps == 128


# --- Loco info X-bus routing (§4.4, X-Header 0xEF) ---------------------------


def test_decode_xbus_routes_loco_info():
    payload = build_loco_info(3, forward=True, step=1, speed_steps=128)[4:]
    result = decode_xbus(payload)
    assert result is not None
    header, decoded = result
    assert header == HDR_LOCO_INFO
    assert isinstance(decoded, LocoInfo)


def test_parse_datagram_surfaces_loco_info():
    dgram = build_loco_info(7, forward=False, step=5, speed_steps=128)
    (info,) = parse_datagram(dgram)
    assert isinstance(info, LocoInfo)
    assert info.address == 7
    assert info.forward is False
    assert info.speed == 5


# --- Seam guard: no HA / socket / asyncio imports ---------------------------


def test_codec_has_no_forbidden_imports():
    src = Path(protocol.__file__).read_text()
    for forbidden in ("import asyncio", "import socket", "homeassistant"):
        assert forbidden not in src, f"protocol.py must not reference {forbidden!r}"
