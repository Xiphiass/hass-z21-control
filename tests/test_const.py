"""Unit tests for the HA-layer presentation helpers (no Home Assistant needed)."""

from __future__ import annotations

from custom_components.z21.const import (
    HW_TYPE_NAMES,
    format_fw_version,
    hw_type_name,
)


def test_format_fw_version_bcd():
    # Spec contract: raw 0x0143 (BCD) => "1.43".
    assert format_fw_version(0x0143) == "1.43"
    assert format_fw_version(0x0100) == "1.00"
    assert format_fw_version(0x0142) == "1.42"


def test_hw_type_name_known():
    assert hw_type_name(0x00000201) == HW_TYPE_NAMES[0x00000201]


def test_hw_type_name_unknown_hex_fallback():
    assert hw_type_name(0x00000999) == "Z21 (0x00000999)"
