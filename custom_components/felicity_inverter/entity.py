"""Base entity."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FelicityCoordinator


def path(data: dict[str, Any], key: str, row: int = 0, col: int = 0) -> Any:
    """Read data[key][row][col] defensively."""
    try:
        return data[key][row][col]
    except (KeyError, IndexError, TypeError):
        return None


class FelicityEntity(CoordinatorEntity[FelicityCoordinator]):
    """Common device info and unique id handling."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FelicityCoordinator, key: str) -> None:
        super().__init__(coordinator)
        serial = str(coordinator.data.get("DevSN") or coordinator.config_entry.unique_id)
        self._attr_unique_id = f"{serial}_{key}"
        info = coordinator.stick_info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer="Felicity Solar",
            name="Felicity Inverter",
            model=f"Type {coordinator.data.get('Type')} / {coordinator.data.get('SubType')}",
            serial_number=serial,
            sw_version=f"CommVer {coordinator.data.get('CommVer')}",
            configuration_url=None,
            connections=set(),
            hw_version=f"WiFi {info.get('wifiSN') or coordinator.data.get('wifiSN')}",
        )
