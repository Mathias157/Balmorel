# Handover: UC ramping under RMIP (for `great_netzero_evinfra`)

Apply this to a local branch tracking `origin/great_netzero_evinfra`, on top of commit 27a3b7c7 ("Fixed ramping equations so RMIP doesn't result in unit on/off cheating"). The decision and reasoning are in `docs/adr/0003-uc-ramping-under-relaxation.md` on the `backcast` branch; copy that ADR along with this change.

## Problem

27a3b7c7 does not stop the cheat it was meant to stop. Under RMIP, `QUCRAMPU`/`QUCRAMPD` still contain the expanded-gradient terms `GDUCGMIN*VUCU` and `GDUCGMIN*VUCD`. A fractional start-up or shutdown of `x` units lets output move by an extra `GDUCGMIN*x` within one step, on top of the ramp rate. For nuclear (`GDUCGMIN` = 0.4, `GDUCRAMPD` = 0.125/h) that is several hours of ramping in one hour. The available-capacity bound that 27a3b7c7 introduced is at least as loose as the original `VUCON` bound, so it made ramping looser rather than tighter.

## Change

There are four equation bodies in `base/addons/unitcommitment/bb4/uc_eqndecdef.inc`: `QUCRAMPU` and `QUCRAMPD`, each in the `SEASONALLINKUC` block and in the plain block. In each one, replace the bracket between `=L=` and `* scale unit input capacity` with the following. This is for ramping up; the four labels must be unique (`QUCRAMPU_1`, `QUCRAMPD_2`, `QUCRAMPU_3`, `QUCRAMPD_4`):

```gams
     (
$ifi %SOLVETYPE%==MIP $goto QUCRAMPU_1_MIP
* LP/RMIP: a pure ramp rate on available capacity (see docs/adr/0003-uc-ramping-under-relaxation.md).
* The MIP expanded gradient (GDUCGMIN*VUCU) is left out: with a fractional VUCU the relaxation could
* start/shut down a fraction of a unit to move output faster than the ramp rate.
         GDATA(IGUC,'GDUCRAMPU')*((GKFX(IY411,IA,IGUC)
$ifi %DECOM%==yes   -VDECOM_EXO_ACCUM(IY411,IA,IGUC)$IGDECOMEXOPOT(IY411,IA,IGUC)
+VGKNACCUMNET(IY411,IA,IGUC)$(IAGK_HASORPOT(IY411,IA,IGUC) AND IAGKN(IA,IGUC)))/GDATA(IGUC,'GDUCUNITSIZE')*(1$(NOT IGKRATE(IA,IGUC,S,T)) + IGKRATE(IA,IGUC,S,T)))
$goto QUCRAMPU_1_END
$label QUCRAMPU_1_MIP
* units under start up have an expanded gradient
         GDATA(IGUC,'GDUCGMIN')*VUCU(IY411,IA,IGUC,S,T)
* up gradient of units on at t excluding units under start up
        + GDATA(IGUC,'GDUCRAMPU')*(VUCON(IY411,IA,IGUC,S,T) - VUCU(IY411,IA,IGUC,S,T))
$label QUCRAMPU_1_END
* scale unit input capacity
```

For ramping down, use `GDUCRAMPD`, `VUCD` and the comment "units under shut down", and make the MIP line `+ GDATA(IGUC,'GDUCRAMPD')*VUCON(IY411,IA,IGUC,S,T)`.

The MIP branch is the original (pre-27a3b7c7) formulation. The LP/RMIP branch is 27a3b7c7's available-capacity term with the expanded gradient (and the `- VUCU` inside it) removed. Apart from these four bodies, `uc_eqndecdef.inc` was identical on the two branches when this was written (2026-10-16). So once the `backcast` commit exists, `git checkout backcast -- base/addons/unitcommitment/bb4/uc_eqndecdef.inc` applies the whole change. Check `git diff` afterwards to confirm that only the ramp bodies changed.

## Effect on existing GREAT runs

The equation is only generated when `CHRONOHOUR*GDUCRAMP < 1`.

- **6-hour full-year runs:** if nuclear in the GREAT data has `6*GDUCRAMPD >= 1`, the equation doesn't exist there and those runs are unaffected. Otherwise the cheat could add at most `1 - 6*GDUCRAMPD` of capacity per step, limited by min-down-time and start-up costs. With 0.125/h that is ≤25% per step.
- **Hourly rolling runs:** fully affected. Apply the change before submitting them. They import storage and hydro targets from the full-year run, so a small part of any full-year distortion still carries over.

## Verification

1. Compile: `gams Balmorel a=c` with an RMIP `balopt.opt` that has `UnitComm yes`.
2. Run one season at hourly resolution with and without the change, and compare the largest hourly change in French nuclear output with `GDUCRAMPU/D × available capacity`. After the change it must never be larger.
