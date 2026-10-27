---
status: accepted
---

# 5. Finite prices for CO2 and G2V-infrastructure slacks, as an option

Under `vqdebug`, every slack costs `PENALTYQ` (1e9). Two of them are not debugging devices when capacities are fixed (an operational simulation with `import_results`, `TechInvest` off):

- `VQLIMCO2NA` / `VQLIMCO2ROLLS` / `VQCCS_STORAGE` cost `PENALTYQ*IOF0001`, i.e. 1e6 money/t (GREAT docs/adr/0060, 0084). With `ADDBACKUPGEN`, any shortfall in firm capacity is met by gas-fired backup, which overshoots a net-zero or negative CO2 limit.
- `VG2VINFRASLACK` costs `PENALTYQ` per MW and time step, unweighted (GREAT docs/adr/0066), so its cost depends on the time resolution. It fires whenever the fixed charging infrastructure is smaller than the charging the simulation needs.

When capacities come from a coarse investment run and are scored in a full-year operational simulation, these penalties outweigh every real cost by orders of magnitude: a test run gave 6.6e9 Mmoney against about 4e4 Mmoney of system cost. The score then only records that a penalty fired, not how far off the capacities were.

We added two options, both empty by default, so existing runs are unchanged:

- `VQCO2PRICE` (money/t) prices CO2 above a CO2 limit or the CCS storage limit. It enters inside `PENALTYQ*(...)` as `VQCO2PRICE/PENALTYQ`, so the net coefficient is the price.
- `G2VSLACKPRICE` (money/MWh) prices G2V charging above the infrastructure capacity, weighted by `IHOURSINST`, so its cost no longer depends on the number of time steps.

Both are read only if set and non-empty, so option files without them still compile.

## Consequences

- With the options set, the CO2 limit becomes a soft limit with a recourse cost, e.g. buying direct air capture. The price must exceed the CO2 shadow price of the investment runs being scored, or a scored run can overshoot the limit for less than it would cost to meet it.
- The G2V price is a scarcity price per MWh, not a capacity cost. If the slack is used in many hours, it costs far more than building the missing chargers would.
- The other `vqdebug` slacks keep `PENALTYQ`, since a solution that uses them is not meaningful.

## Considered Options

- **Lower `PENALTYQ`**: rejected because it would also make energy-balance and other debugging slacks cheap.
- **Recourse charging capacity** (a variable per region bounding `VG2VINFRASLACK` in every time step, priced at the annualised charger cost): more faithful, since missing chargers cost capacity, not energy. Not chosen for now, because it adds an equation per region and time step. It is the next step if the G2V price dominates scores.
