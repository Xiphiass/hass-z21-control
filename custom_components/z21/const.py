"""Constants and presentation helpers for the Z21 Home Assistant integration.

This is the HA-layer home for anything that turns raw codec values into
user-facing text. The pure codec (``protocol.py``) deliberately leaves
presentation to the caller (see ``protocol.HwInfo``), so the BCD firmware
formatting and hardware-type naming live here rather than in the codec.
"""

from __future__ import annotations

from .client import DEFAULT_PORT

__all__ = [
    "DOMAIN",
    "DEFAULT_PORT",
    "CONF_SERIAL",
    "CONF_HW_TYPE",
    "CONF_FW_VERSION",
    "MANUFACTURER",
    "HW_TYPE_NAMES",
    "hw_type_name",
    "format_fw_version",
]

DOMAIN = "z21"

# Config-entry data keys. Host uses Home Assistant's own ``CONF_HOST``.
CONF_SERIAL = "serial"
CONF_HW_TYPE = "hw_type"
CONF_FW_VERSION = "fw_version"

# Generic — the integration targets Z21-compatible stations, not one vendor
# (CONTEXT.md "Domain").
MANUFACTURER = "Roco/Fleischmann"

# Known LAN_GET_HWINFO HwType codes (Z21 LAN protocol spec 2.20). Unknown types
# fall back to a hex string via ``hw_type_name``.
HW_TYPE_NAMES: dict[int, str] = {
    0x00000200: "Z21 (black, 2012)",
    0x00000201: "Z21 (black, 2013+)",
    0x00000202: "SmartRail (2012)",
    0x00000203: "z21 small (white, 2013)",
    0x00000204: "z21start (2016)",
    0x00000205: "Z21 Single Booster (10806)",
    0x00000206: "Z21 Dual Booster (10807)",
    0x00000211: "Z21 XL Series (2020)",
    0x00000212: "XL Booster (10869)",
    0x00000301: "Z21 SwitchDecoder (10836)",
    0x00000302: "Z21 SignalDecoder (10836)",
}


def hw_type_name(hw_type: int) -> str:
    """Friendly model name for a HwType code, hex fallback if unknown."""
    return HW_TYPE_NAMES.get(hw_type, f"Z21 (0x{hw_type:08X})")


def format_fw_version(fw_version: int) -> str:
    """Format a BCD-encoded firmware version as ``"major.minor"``.

    The Z21 encodes the firmware version as BCD (spec 2.20), e.g. the raw value
    ``0x0143`` represents V1.43. The high byte holds the major number and the
    low byte the (two-digit) minor number.
    """
    major = _bcd(fw_version >> 8 & 0xFF)
    minor = _bcd(fw_version & 0xFF)
    return f"{major}.{minor:02d}"


def _bcd(byte: int) -> int:
    """Decode a single BCD-encoded byte to its integer value."""
    return (byte >> 4) * 10 + (byte & 0x0F)
