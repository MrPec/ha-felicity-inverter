"""Constants for the Felicity Inverter (local) integration."""

from __future__ import annotations

DOMAIN = "felicity_inverter"

DEFAULT_PORT = 53970
DEFAULT_SCAN_INTERVAL = 15  # seconds
MIN_SCAN_INTERVAL = 5

CONF_SCAN_INTERVAL = "scan_interval"

QUERY_REALTIME = b"wifilocalMonitor:get dev real infor"
QUERY_DATE = b"wifilocalMonitor:get Date"
ACK = b"."

CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 8.0

# Bit n of the `warn` field corresponds to warning code n of the T-REX
# warning table. Verified for bit 25 (phase sequence error) on a
# T-REX-10KHP3G01; the other names are taken from the same table.
# Bits without a table entry are reported as "Warning bit <n>".
WARNING_BITS: dict[int, str] = {
    7: "Low battery",
    9: "Overload",
    25: "Phase sequence error",
}
PHASE_SEQUENCE_BIT = 25


def active_warning_bits(warn: int | None) -> list[int]:
    """Return the set bit positions of the warn field."""
    if not isinstance(warn, int) or warn <= 0:
        return []
    return [bit for bit in range(32) if warn >> bit & 1]


def warning_names(warn: int | None) -> list[str]:
    """Human readable names for the active warning bits."""
    return [WARNING_BITS.get(bit, f"Warning bit {bit}") for bit in active_warning_bits(warn)]
