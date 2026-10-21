# Felicity Inverter (local) for Home Assistant

Reads a **Felicity Solar hybrid inverter** directly from its USB WiFi stick over the local network. No cloud, no extra hardware, no Node-RED.

Tested with a 3-phase inverter that reports `Type 81 / SubType 12818` through a stick with hostname `FLS_BL602-xxxxxx`.

## How it works

The stick listens on TCP port `53970`. The integration sends the ASCII command `wifilocalMonitor:get dev real infor`, reads one JSON object back and acknowledges with `.`. Every poll uses a fresh connection, default interval 15 s.

The transport is the same one used by [xpoh697/FelicityESS](https://github.com/xpoh697/FelicityESS) for Felicity batteries. That integration only maps battery packs (`Type 112`); this one maps the inverter fields.

## Installation

HACS → three dots → *Custom repositories* → `https://github.com/MrPec/ha-felicity-inverter`, category *Integration*. Install, restart Home Assistant, then *Settings → Devices & services → Add integration → Felicity Inverter (local)* and enter the stick's IP.

Give the stick a fixed DHCP lease.

## Entities

| Entity | Source field | Notes |
|---|---|---|
| PV power | `PV[2]` summed | W, all MPPTs |
| PV1 power / voltage / current | `PV[2][0]`, `PV[0][0]`/10, `PV[1][0]`/10 | PV2 disabled by default |
| Grid voltage L1-L3, current L1-L3, frequency, power | `ACin` | grid side |
| Output current L1-L3, power, apparent power | `ACout` | load side, voltage/frequency disabled by default |
| Load | `lPerc` | % of rating |
| Inverter temperature, Temperature 2 | `Temp[0][0]`/10, `Temp[0][3]`/10 | |
| Work mode / warning / fault code | `workM`, `warn`, `fault` | diagnostic, raw codes |
| Active warnings | `warn` bits | text, e.g. `Phase sequence error` |
| Fault / Warning | `fault != 0` / any `warn` bit | binary, problem; attributes list the bits |
| Phase sequence error | `warn` bit 25 | binary, problem |

### Warning bits

Bit *n* of `warn` matches warning code *n* on the inverter display. This is verified for bit 25: a T-REX-10KHP3G01 with two swapped grid phases showed a flashing `25` on the LCD and had bit 25 set; after swapping L2/L3 the bit cleared, `workM` went from 3 to 5 and the inverter synchronised to the grid. While bit 25 is set the inverter does not feed the grid and throttles PV to its own consumption.

Names for 7 (low battery) and 9 (overload) come from the warning table of the manual. Other bits are shown as `Warning bit <n>`; on the test unit bits 4 and 6 were set while the app showed *CommOffline* (no smart meter) and *Derating by voltage*.
| WiFi signal | stick `rssi` | disabled by default |

There are no energy counters in the realtime answer. For the Energy dashboard create an **Integral** helper (Riemann sum, left method, kWh) on *PV power*.

The mapping is derived from observed values and the field layout; codes for `workM`, `warn` and `fault` are not decoded yet. The diagnostics download contains the raw snapshot with serial numbers redacted. Please open an issue with one if your model reports different values.

## License

MIT
