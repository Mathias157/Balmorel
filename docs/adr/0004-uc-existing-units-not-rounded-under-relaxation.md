---
status: accepted
---

# 4. Existing UC units are not rounded up to whole units under LP/RMIP

Existing unit-commitment capacity is counted in whole units, using `CEIL(GKFX/GDUCUNITSIZE)`, in two places. The first is the variable bounds `VUCON.UP` and `VUCON_STOLOAD.UP` (`base/addons/unitcommitment/bb4/uc_sim.inc`), from which `VGE_T.UP`/`VGH_T.UP` and storage loading bounds are derived. The second is the equations `QUCVUCON_EXISTING`, `QUCVUCON_EXISTING_STOLOAD`, `QUCMAINTMIN` and `QUCDT` (`uc_eqndecdef.inc`). The bounds always apply. The equations only apply with `PLANNED_MAINTENANCE` (and only for technologies with `GDPLANMAINT`) or `MINSHUTDOWNTIME`, so fixing only the equations leaves the extra capacity in every other case. The core capacity limit for UC technologies is replaced by `GDUCUNITSIZE*VUCON` (`uc_qgcvgext.inc`). So whenever `GKFX` is not a multiple of the unit size, output can go above `GKFX` by up to one unit. In GREAT's base runs, 6 MW of wood condensing in Serbia produced 400 MW and 50 MW of CCGT in DE4-E produced 700 MW. Summed over all pairs at their maximum output, that is 24 GW above installed capacity in the 2030 full-year run. Rounding up is a modelling choice for a true MIP, where the number of units has to be an integer. Under LP/RMIP the fractional count is already allowed, so the rounding only adds capacity.

We decided that when `SOLVETYPE` is anything other than `MIP`, existing units are counted as `GKFX/GDUCUNITSIZE` in both the bounds and the equations. Under `MIP`, `CEIL` is kept. The bounds on `VUCU`, `VUCD` and the maintenance variables keep `CEIL` under both, since they don't add capacity: output is limited through `VUCON`.

## Consequences

- Under LP/RMIP, UC output never exceeds installed capacity, which matches non-UC technologies and the endogenous-capacity equation `QUCVUCON`. That equation never used `CEIL`.
- Results change most where existing capacity is small compared to the unit size: leftover gas/biomass and small nuclear countries. Adequacy and flexibility indicators in those countries lose capacity that was never in the data.
- Investment runs with `UnitComm yes` no longer under-invest because of the extra capacity. Runs with `UnitComm` off never saw it.

## Considered Options

- **Round down (`FLOOR`) under RMIP:** rejected. It removes real capacity, and all of it when `GKFX` is less than one unit.
- **Keep `CEIL` and add a separate `VGE <= GKFX` limit for UC technologies:** rejected. It adds an equation per hour to keep a bound the relaxation doesn't need, and minimum load would still apply to the phantom unit.
- **Change `GDUCUNITSIZE` in the data so capacities are whole numbers of units:** rejected. Unit size also sets minimum load and start-up costs per unit, and the leftover capacities come from many data sources.
