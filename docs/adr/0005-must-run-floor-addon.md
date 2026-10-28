---
status: accepted
---

# 5. Observed must-run enters as a penalized weekly floor per zone and fuel group

The 2023 backcast never reaches a price of 0 in DE, which observed 311 hours at or below 0, and its DE biomass makes 0.6 TWh against 37.4 observed. In those 311 hours, DE thermal plants still ran at about 13 GW (lignite 3.8, biomass 3.9, gas 2.6, coal 1.8 GW). That output ran for reasons Balmorel does not model: heat and steam obligations, system services, long start-ups, fixed contracts and subsidies. A cost-minimizing dispatch switches it off, so the price floor and the bottom of the fossil mix are wrong for structural reasons, not because of a data error. We decided to add a `MUSTRUN` addon (`base/addons/mustrun`). Its equation `QMUSTRUN` requires the output of a zone's condensing, back-pressure and extraction technologies of one fuel group to be at least `MUSTRUN_FLOOR(zone, group, season)` in every time step of that season. A slack, `VMUSTRUN_SLACK`, costs `MUSTRUN_PENALTY` per MWh short, by default 300 €2016/MWh. A zone is a set of regions (`MUSTRUN_ZONE_RRR`), and a group is a set of fuels (`MUSTRUN_GROUP_FFF`). Both sets and the floors are data files, written for a backcast by pybalmorel's `must-run-floor` command. The backcast opt files switch the addon on when `data/MUSTRUN_FLOOR.inc` exists; base keeps it off.

## Consequences

- The floor fixes the bottom of the fossil mix by construction, about 209 of the observed fossil TWh in 2023 at pybalmorel's default threshold (40 €/MWh, 4 hours a week). Only the mix above it is a validation metric (see `CONTEXT.md`, Must-run floor).
- Back-pressure CHP held at a floor produces heat as well, which pushes other heat production out, including electric heating. Electric heating is a validation metric, so it has to be read with that in mind.
- The penalty is a model parameter, not data, so its default sits in the addon (`mustrun_pardefine.inc`). `base/data` is not tracked, and a backcast that wants another value writes `data/MUSTRUN_PENALTY.inc`.
- The slack is not in MainResults. Its use shows up as output below the floor in `PRO_YCRAGFST`.
- The addon adds one equation per zone, group and time step of the weeks with a floor. It works with any `SOLVETYPE` and without unit commitment.
- So far it has only been compiled with the backcast data, not solved.

## Considered Options

- **Hard constraint without slack:** rejected. A floor can be infeasible in a given time step: back-pressure CHP needs a heat sink, the group's units can all be rated down by outages, and the floor comes from a different data source than the capacities. Infeasibility would stop the run instead of showing where it happens.
- **Minimum load through unit commitment (`GDUCGMIN`, `UnitComm yes`):** rejected. Minimum load only applies to units that are on, and the model can still switch them off, which is exactly what it does at low prices. Unit commitment would also make the backcast much slower to solve.
- **Annual minimum fuel use (`GMINF`):** rejected. It fixes how much fuel is burnt in the year, not when, so the model burns it in the expensive hours and the low-price hours stay as they were.
- **Lower bounds on `VGE_T` per technology:** rejected. ENTSO-E reports output per fuel group and bidding zone, not per Balmorel technology or area, so any split to technologies would be invented.
- **Hourly floor (the observed output in every hour):** rejected. It would fix most of the fossil mix to observed data and leave nothing to validate. A weekly floor taken from the week's lowest hour only covers what ran in every hour of that week.
- **Switch in base's `balopt.opt` with data in `base/data`:** rejected. The floor is backcast-year data, so the switch follows the data file's existence, like the other ENTSO-E overrides in `backcast/data`.
