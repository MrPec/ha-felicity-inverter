"""Binary sensors for the Felicity inverter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import PHASE_SEQUENCE_BIT, active_warning_bits, warning_names
from .coordinator import FelicityConfigEntry, FelicityCoordinator
from .entity import FelicityEntity


def _fault(d: dict[str, Any]) -> bool | None:
    fault = d.get("fault")
    return None if fault is None else fault != 0


def _warning(d: dict[str, Any]) -> bool | None:
    warn = d.get("warn")
    return None if warn is None else bool(active_warning_bits(warn))


def _phase_sequence(d: dict[str, Any]) -> bool | None:
    warn = d.get("warn")
    return None if warn is None else PHASE_SEQUENCE_BIT in active_warning_bits(warn)


@dataclass(frozen=True, kw_only=True)
class FelicityBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSORS: tuple[FelicityBinaryDescription, ...] = (
    FelicityBinaryDescription(
        key="fault", name="Fault", device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC, value_fn=_fault,
    ),
    FelicityBinaryDescription(
        key="warning", name="Warning", device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC, value_fn=_warning,
    ),
    FelicityBinaryDescription(
        key="phase_sequence_error", name="Phase sequence error",
        device_class=BinarySensorDeviceClass.PROBLEM, value_fn=_phase_sequence,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FelicityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(FelicityBinarySensor(entry.runtime_data, d) for d in BINARY_SENSORS)


class FelicityBinarySensor(FelicityEntity, BinarySensorEntity):
    entity_description: FelicityBinaryDescription

    def __init__(self, coordinator: FelicityCoordinator, description: FelicityBinaryDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key not in ("fault", "warning"):
            return None
        d = self.coordinator.data or {}
        return {
            "fault_code": d.get("fault"),
            "warning_code": d.get("warn"),
            "warning_bits": active_warning_bits(d.get("warn")),
            "warnings": warning_names(d.get("warn")),
        }
