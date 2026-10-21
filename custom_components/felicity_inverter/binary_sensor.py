"""Binary sensors for the Felicity inverter."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import FelicityConfigEntry, FelicityCoordinator
from .entity import FelicityEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FelicityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([FelicityFault(entry.runtime_data)])


class FelicityFault(FelicityEntity, BinarySensorEntity):
    """On when the inverter reports a non-zero fault code."""

    _attr_name = "Fault"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: FelicityCoordinator) -> None:
        super().__init__(coordinator, "fault")

    @property
    def is_on(self) -> bool | None:
        fault = self.coordinator.data.get("fault")
        return None if fault is None else fault != 0

    @property
    def extra_state_attributes(self) -> dict[str, int | None]:
        return {
            "fault_code": self.coordinator.data.get("fault"),
            "warning_code": self.coordinator.data.get("warn"),
        }
