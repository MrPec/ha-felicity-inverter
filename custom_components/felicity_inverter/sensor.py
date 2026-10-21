"""Sensors for the Felicity inverter.

Field mapping (Type 81, 3-phase hybrid, observed on firmware CommVer 1):

  PV     [[V*10 per MPPT], [A*10 per MPPT], [W per MPPT], [...]]
  ACin   [[V*10 L1..L3], [A*10 L1..L3], [Hz*100 L1..L3], [W, VA], [...]]   grid side
  ACout  [[V*10 L1..L3], [A*10 L1..L3], [Hz*100 L1..L3], [W, VA, ?], [...]] load side
  Temp   [[inverter*10, -, -, ambient*10, ...]]
  busVp / busVn   DC bus +/- in V*10
  lPerc  load in percent of rating
  workM  operating mode code, warn / fault bit fields
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import FelicityConfigEntry, FelicityCoordinator
from .entity import FelicityEntity, path


def _scaled(key: str, row: int, col: int, factor: float) -> Callable[[dict[str, Any]], Any]:
    def fn(d: dict[str, Any]) -> Any:
        v = path(d, key, row, col)
        return None if v is None else round(v * factor, 3)

    return fn


def _pv_total(d: dict[str, Any]) -> Any:
    try:
        return sum(int(x) for x in d["PV"][2])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


@dataclass(frozen=True, kw_only=True)
class FelicitySensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    stick: bool = False  # value comes from stick info instead of realtime data


V, A, HZ, W, VA = (
    UnitOfElectricPotential.VOLT,
    UnitOfElectricCurrent.AMPERE,
    UnitOfFrequency.HERTZ,
    UnitOfPower.WATT,
    UnitOfApparentPower.VOLT_AMPERE,
)
MEAS = SensorStateClass.MEASUREMENT


def _voltage(key: str, name: str, row: int, col: int, enabled: bool = True) -> FelicitySensorDescription:
    return FelicitySensorDescription(
        key=key, name=name, device_class=SensorDeviceClass.VOLTAGE, native_unit_of_measurement=V,
        state_class=MEAS, suggested_display_precision=1, entity_registry_enabled_default=enabled,
        value_fn=_scaled({"pv": "PV", "grid": "ACin", "out": "ACout"}[key.split("_")[0]], row, col, 0.1),
    )


SENSORS: tuple[FelicitySensorDescription, ...] = (
    # PV
    FelicitySensorDescription(
        key="pv_power", name="PV power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=W, state_class=MEAS, value_fn=_pv_total,
    ),
    FelicitySensorDescription(
        key="pv1_power", name="PV1 power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=W, state_class=MEAS, value_fn=_scaled("PV", 2, 0, 1),
    ),
    FelicitySensorDescription(
        key="pv1_voltage", name="PV1 voltage", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=V, state_class=MEAS, suggested_display_precision=1,
        value_fn=_scaled("PV", 0, 0, 0.1),
    ),
    FelicitySensorDescription(
        key="pv1_current", name="PV1 current", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=A, state_class=MEAS, suggested_display_precision=1,
        value_fn=_scaled("PV", 1, 0, 0.1),
    ),
    FelicitySensorDescription(
        key="pv2_power", name="PV2 power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=W, state_class=MEAS, entity_registry_enabled_default=False,
        value_fn=_scaled("PV", 2, 1, 1),
    ),
    FelicitySensorDescription(
        key="pv2_voltage", name="PV2 voltage", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=V, state_class=MEAS, suggested_display_precision=1,
        entity_registry_enabled_default=False, value_fn=_scaled("PV", 0, 1, 0.1),
    ),
    # Grid side
    *(
        FelicitySensorDescription(
            key=f"grid_voltage_l{i + 1}", name=f"Grid voltage L{i + 1}",
            device_class=SensorDeviceClass.VOLTAGE, native_unit_of_measurement=V,
            state_class=MEAS, suggested_display_precision=1, value_fn=_scaled("ACin", 0, i, 0.1),
        )
        for i in range(3)
    ),
    *(
        FelicitySensorDescription(
            key=f"grid_current_l{i + 1}", name=f"Grid current L{i + 1}",
            device_class=SensorDeviceClass.CURRENT, native_unit_of_measurement=A,
            state_class=MEAS, suggested_display_precision=1, value_fn=_scaled("ACin", 1, i, 0.1),
        )
        for i in range(3)
    ),
    FelicitySensorDescription(
        key="grid_frequency", name="Grid frequency", device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=HZ, state_class=MEAS, suggested_display_precision=2,
        value_fn=_scaled("ACin", 2, 0, 0.01),
    ),
    FelicitySensorDescription(
        key="grid_power", name="Grid power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=W, state_class=MEAS, value_fn=_scaled("ACin", 3, 0, 1),
    ),
    # Output / load side
    *(
        FelicitySensorDescription(
            key=f"output_voltage_l{i + 1}", name=f"Output voltage L{i + 1}",
            device_class=SensorDeviceClass.VOLTAGE, native_unit_of_measurement=V,
            state_class=MEAS, suggested_display_precision=1, entity_registry_enabled_default=False,
            value_fn=_scaled("ACout", 0, i, 0.1),
        )
        for i in range(3)
    ),
    *(
        FelicitySensorDescription(
            key=f"output_current_l{i + 1}", name=f"Output current L{i + 1}",
            device_class=SensorDeviceClass.CURRENT, native_unit_of_measurement=A,
            state_class=MEAS, suggested_display_precision=1, value_fn=_scaled("ACout", 1, i, 0.1),
        )
        for i in range(3)
    ),
    FelicitySensorDescription(
        key="output_power", name="Output power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=W, state_class=MEAS, value_fn=_scaled("ACout", 3, 0, 1),
    ),
    FelicitySensorDescription(
        key="output_apparent_power", name="Output apparent power",
        device_class=SensorDeviceClass.APPARENT_POWER, native_unit_of_measurement=VA,
        state_class=MEAS, value_fn=_scaled("ACout", 3, 1, 1),
    ),
    FelicitySensorDescription(
        key="output_frequency", name="Output frequency", device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=HZ, state_class=MEAS, suggested_display_precision=2,
        entity_registry_enabled_default=False, value_fn=_scaled("ACout", 2, 0, 0.01),
    ),
    FelicitySensorDescription(
        key="load_percent", name="Load", native_unit_of_measurement=PERCENTAGE,
        state_class=MEAS, value_fn=lambda d: d.get("lPerc"),
    ),
    # Device
    FelicitySensorDescription(
        key="temperature_inverter", name="Inverter temperature",
        device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=MEAS, suggested_display_precision=1, value_fn=_scaled("Temp", 0, 0, 0.1),
    ),
    FelicitySensorDescription(
        key="temperature_2", name="Temperature 2",
        device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=MEAS, suggested_display_precision=1, entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_scaled("Temp", 0, 3, 0.1),
    ),
    FelicitySensorDescription(
        key="bus_voltage_positive", name="DC bus voltage +", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=V, state_class=MEAS, suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False,
        value_fn=lambda d: None if d.get("busVp") is None else d["busVp"] / 10,
    ),
    FelicitySensorDescription(
        key="bus_voltage_negative", name="DC bus voltage -", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=V, state_class=MEAS, suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False,
        value_fn=lambda d: None if d.get("busVn") is None else d["busVn"] / 10,
    ),
    FelicitySensorDescription(
        key="work_mode", name="Work mode code", entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("workM"),
    ),
    FelicitySensorDescription(
        key="warning_code", name="Warning code", entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("warn"),
    ),
    FelicitySensorDescription(
        key="fault_code", name="Fault code", entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("fault"),
    ),
    FelicitySensorDescription(
        key="wifi_rssi", name="WiFi signal", device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT, state_class=MEAS,
        entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False,
        stick=True, value_fn=lambda d: d.get("rssi"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FelicityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(FelicitySensor(coordinator, d) for d in SENSORS)


class FelicitySensor(FelicityEntity, SensorEntity):
    entity_description: FelicitySensorDescription

    def __init__(self, coordinator: FelicityCoordinator, description: FelicitySensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        source = self.coordinator.stick_info if self.entity_description.stick else self.coordinator.data
        return self.entity_description.value_fn(source or {})
