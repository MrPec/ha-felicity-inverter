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
