"""Diagnostics: raw snapshot for mapping new fields."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import FelicityConfigEntry

TO_REDACT = {"wifiSN", "DevSN"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FelicityConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "realtime": async_redact_data(coordinator.data or {}, TO_REDACT),
        "stick": async_redact_data(coordinator.stick_info or {}, TO_REDACT),
    }
