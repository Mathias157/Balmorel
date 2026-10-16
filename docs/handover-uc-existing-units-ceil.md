# Handover: existing UC units rounded up to whole units under RMIP

Apply this to any branch that runs unit commitment as LP/RMIP. It was first made on `great_netzero_evinfra` (GREAT submodule, 2026-10-16), together with the ramp fix in `docs/handover-uc-ramping-relaxation.md`. The decision and reasoning are in `docs/adr/0004-uc-existing-units-not-rounded-under-relaxation.md`; copy that ADR along with this change.

## Problem

Existing unit-commitment capacity (`GKFX` without investment or decommissioning potential) is counted in whole units with `CEIL(GKFX/GDUCUNITSIZE)`. That happens both in the variable bounds `VUCON.UP`/`VUCON_STOLOAD.UP` (`uc_sim.inc`) and in four equations (`uc_eqndecdef.inc`). The core capacity limit for UC technologies is replaced by `GDUCUNITSIZE*VUCON` (`uc_qgcvgext.inc`), and `VGE_T.UP`/`VGH_T.UP` are set to `GDUCUNITSIZE*VUCON.UP`. So nothing else stops output from reaching the rounded-up capacity. Under RMIP the extra capacity can be used freely:

- 6 MW of `GNR_ST_WOOD_CND_E-50` in RS_A produced 400 MW; 50 MW of `GNR_CC_NGAS_CND_E-56` in DE4-E_A produced 700 MW.
- Nuclear: RO 1.3 → 1.8 GW, SI 0.70 → 1.2 GW, BG 1.0 → 1.2 GW.
- GREAT base runs, summed over all area-generation pairs at their maximum output: 24 GW above installed capacity in `_F2030`, 8.7 GW in `_F2050`, and 11.1 GW in `_R2050`. In all three, no output exceeded the rounded-up capacity, so `CEIL` explains all of it.

## Change

In `base/addons/unitcommitment/bb4/uc_eqndecdef.inc`, every line that starts with `CEIL(` gets a MIP and a non-MIP variant. There are four:

| Equation | Active when |
|---|---|
| `QUCDT` | `MINSHUTDOWNTIME`, existing units only |
| `QUCVUCON_EXISTING` | `PLANNED_MAINTENANCE` |
| `QUCVUCON_EXISTING_STOLOAD` | `PLANNED_MAINTENANCE` |
| `QUCMAINTMIN` | `PLANNED_MAINTENANCE` |

Pattern, shown for `QUCVUCON_EXISTING`:

```gams
$ifi     %SOLVETYPE%==MIP CEIL(GKFX(IY411,IA,IGUC)/GDATA(IGUC,'GDUCUNITSIZE'))
$ifi not %SOLVETYPE%==MIP (GKFX(IY411,IA,IGUC)/GDATA(IGUC,'GDUCUNITSIZE'))
```

Keep each line's own trailing condition or factor unchanged: `$(NOT(SUM(...)) AND NOT(IGDECOMEXOPOT(...)))` on `QUCDT`, `*IGPLANMAINT(IGUC)` on `QUCMAINTMIN`. Put this comment above the first one (`QUCDT`):

```gams
* LP/RMIP: existing units as a fractional unit count, not CEIL - with CEIL the relaxation gets whole units' worth of capacity beyond GKFX (see docs/adr/0004-uc-existing-units-not-rounded-under-relaxation.md)
```

Check: `grep -n "CEIL(" uc_eqndecdef.inc` should only list lines that start with `$ifi     %SOLVETYPE%==MIP`.

**The equations alone are not enough.** `QUCVUCON_EXISTING` is only generated with `PLANNED_MAINTENANCE` and for technologies with `GDPLANMAINT`, and `QUCDT` only with `MINSHUTDOWNTIME` and `GDUCDTMIN > CHRONOHOUR`. In every other case, the binding limit on existing units is the variable bound in `base/addons/unitcommitment/bb4/uc_sim.inc`. Split these four lines the same way, keeping the rest of each line, the `MAX(0,...)` included:

| Line | Bound |
|---|---|
| `VUCON.UP(...) = CEIL(...)` | always |
| `VUCON_STOLOAD.UP(...) = CEIL(...)` | always |
| `$ifi %import_results%==yes $ifi %ADDPLANNEDMAINTENANCE%==yes VUCON.UP(...) = MAX(0,CEIL(...))` | rolling runs importing maintenance |
| same for `VUCON_STOLOAD.UP` | rolling runs importing maintenance |

For the last two, put the `$ifi [not] %SOLVETYPE%==MIP` in front of the existing `$ifi` chain. Put the same comment above the first `VUCON.UP` line. `VGE_T.UP`/`VGH_T.UP` and the storage loading bounds are computed from `VUCON.UP`/`VUCON_STOLOAD.UP`, so they follow automatically. Leave `VUCU.UP`, `VUCD.UP` and the `*MAINT.UP` bounds as `CEIL`: they don't add capacity.

Check: `grep -an "CEIL(" uc_sim.inc` should list no `VUCON.UP`/`VUCON_STOLOAD.UP` line that doesn't start with `$ifi     %SOLVETYPE%==MIP`.

On `backcast`, both files have this change, so `git checkout backcast -- base/addons/unitcommitment/bb4/uc_sim.inc` applies the `uc_sim.inc` part, provided the file doesn't differ between the branches otherwise (check `git diff`).

## Effect on existing runs

- This doesn't depend on time resolution, so every LP/RMIP run with `UnitComm yes` is affected. Runs with `UnitComm` off (e.g. GREAT's investment runs, `balopt_inv.opt`) are not.
- Investment runs with `UnitComm yes` see the extra capacity too. That lowers the capacity the model invests in wherever existing UC capacity isn't a whole number of units.
- The effect is largest where installed capacity is small compared to the unit size: leftover gas/biomass capacity and small nuclear countries. Large fleets change by less than one unit (FR nuclear: 15.6 → 15.5 GW).

## Resolved: existing units always have an upper bound

An earlier version of this handover listed an open question: without `PLANNED_MAINTENANCE` (GREAT's rolling runs), or for technologies without `GDPLANMAINT`, no equation bounds `VUCON` for existing-only units. The missing bound is `VUCON.UP` in `uc_sim.inc`. It always exists, but it was also `CEIL`ed, which is why no output exceeded the rounded-up capacity in `base_R2050`. With the `uc_sim.inc` change above, it is `GKFX/GDUCUNITSIZE` under LP/RMIP too.

## Verification

1. Compile: `gams Balmorel action=c` with `SOLVETYPE` RMIP and MIP. In the RMIP listing, `QUCVUCON_EXISTING` must show `(GKFX(...)/GDATA(...,'GDUCUNITSIZE'))` without `CEIL`, and the `VUCON.UP` line must appear without a `$ifi` prefix and without `CEIL`. (The listing contains non-ASCII bytes, so use `grep -a`.)
2. After a run, compare each UC generation's highest electricity output (`PRO_YCRAGFST`) with its installed capacity (`G_CAP_YCRAF`). After the change, none may exceed installed capacity (beyond solver tolerance).
