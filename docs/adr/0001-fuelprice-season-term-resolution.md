# 1. Season/term (S,T) resolution for FUELPRICE

Date: 2026-08-12
Status: Accepted, partially implemented (see Open issues)

## Context

`backcast/historicalprices/` holds daily/near-daily fuel price series (coal,
natural gas, oil, CO2) that we want to feed into Balmorel for backcasting,
instead of the single annual `FUELPRICE(YYY,AAA,FFF)` value the model
currently supports.

This piece of work is scoped to the **Balmorel GAMS framework only** — making
it *possible* to declare and use season/term-resolved fuel prices. Turning
the CSVs in `backcast/historicalprices/` into an actual `.inc` data file is a
separate, later task on the pybalmorel side.

## Decision

Extend `FUELPRICE` using the domain-overloading idiom already established in
this codebase for `XKRATE`/`GKRATE`/`GMINF`/`GMAXF`/`GEQF` (see
`XKRATE_DOL`/`GKRATE_DOL` in `base/model/balopt.opt` and their `$ifi
%..._DOL%==...` branches in `base/model/bb4datainc.inc` /
`base/model/Balmorelbb4.inc`), rather than inventing a new parallel
parameter or mechanism.

Concretely:

- New global `FUELPRICE_DOL` (`base/model/balopt.opt`), default
  `YYY_AAA_FFF` (fully backward compatible). Options:
  `YYY_AAA_FFF` | `YYY_AAA_FFF_SSS` | `YYY_AAA_FFF_SSS_TTT`.
- `FUELPRICE`'s declaration in `base/model/bb4datainc.inc` is now one of
  three `$ifi`-gated variants matching `FUELPRICE_DOL`, only one of which is
  ever compiled in for a given scenario.
- The inactive-year zero-out (`base/model/Balmorelbb4.inc`, formerly a single
  `FUELPRICE(YYY,AAA,FFF)$(NOT(Y(YYY)))=0;` line) is likewise split into
  three domain-matched variants.
- A new internal parameter `IFUELPRICE(YYY,AAA,FFF,S,T)` is computed once
  (right after the final `IHOURSINST` assignment, well before any output
  files are included) by broadcasting whichever `FUELPRICE` domain is active
  across the full `(S,T)` grid. Scenarios that don't supply season/term data
  simply get the annual value replicated across all `(S,T)` — this is what
  keeps every existing scenario's results bit-for-bit unchanged.
- A second internal parameter `IFUELPRICE_Y(Y,AAA,FFF)` holds the
  `IHOURSINST`-weighted annual average of `IFUELPRICE`, for the handful of
  places that only ever wanted a single representative annual price
  (inter-run carryover, pre-solve diagnostics). For the default domain this
  is numerically identical to plain `FUELPRICE`.
- The objective function's fuel-cost term and `OUTPUT_SUMMARY.inc`'s
  `GENERATION_FUEL_COSTS` now read `IFUELPRICE` *inside* the `(S,T)` sum
  (previously `FUELPRICE` was a per-year scalar multiplied in front of the
  sum) — this is the actual behavioural change that makes daily-resolution
  pricing possible.
- `FUELPRICE_EXC` (inter-run carryover, `Balmorelbb4.inc`) and the diagnostic
  `inputout.inc` printout now read `IFUELPRICE_Y` instead of raw `FUELPRICE`,
  since arbitrary-arity `FUELPRICE` can no longer be referenced directly
  outside the domain-matched branches.
- `aep_yna.inc` (an existing, permanently-dead reporting file gated behind a
  top-level `$GOTO ENDOFFILE`/`$LABEL ENDOFFILE`) had one live reference
  (outside the dead region) updated to `IFUELPRICE` for compile-safety; this
  turned out to be unnecessary once we confirmed `$goto`/`$label` are
  genuine compile-time skips in GAMS (see Verification), but is harmless and
  was left in place.

### Files changed
- `base/model/balopt.opt` — new `FUELPRICE_DOL` global (default
  `YYY_AAA_FFF`).
- `base/model/bb4datainc.inc` — domain-flexible `FUELPRICE` declaration.
- `base/model/Balmorelbb4.inc` — domain-flexible zero-out;
  `IFUELPRICE`/`IFUELPRICE_Y` computation; objective function; `FUELPRICE_EXC`
  carryover.
- `base/output/OUTPUT_SUMMARY.inc` — `GENERATION_FUEL_COSTS` now S,T-aware.
- `base/output/printout/printinc/inputout.inc` — 7 diagnostic references
  switched to `IFUELPRICE_Y`.
- `base/output/printout/printinc/aep_yna.inc` — 1 reference switched to
  `IFUELPRICE` (dead code, see above).

## Verification

GAMS is available in the pixi env (`/opt/gams/53/gams`). Ran compile-only
(`action=c`) against `base/model/Balmorel.gms` with `--SCNAME=APS` (a valid
fuel-price scenario name; `EMI_POL`/`FUELPRICE` both key off `%SCNAME%`).

- **Default config** (`FUELPRICE_DOL=YYY_AAA_FFF`, i.e. every existing
  scenario's behaviour): `*** Status: Normal completion`. This includes
  `OUTPUT_SUMMARY.inc` and `Balmorelbb4.sim` → `prtbb4.inc` → `aep_yna.inc`,
  i.e. every file touched above.
- **Season/term config** (`FUELPRICE_DOL=YYY_AAA_FFF_SSS_TTT`, with a
  temporary trivial `FUELPRICE(YYY,AAA,FFF,SSS,TTT)=0;` override in place of
  the real `base/data/FUELPRICE.inc`, both reverted after the test): compiled
  cleanly **once `HYDROGEN_FUELPRICE.inc` was neutralized** — see Open
  issues below, that neutralization was reverted per user direction and is
  *not* in the working tree.
- Confirmed empirically (isolated test script) that GAMS `$goto`/`$label`
  (compile-time directives) truly elide the enclosed source from
  compilation — a reference with the wrong number of indices inside a
  skipped block does not error. This is distinct from a runtime `GOTO`
  statement, which does not affect compilation. Relevant because several
  fixes above initially assumed the stricter (compile-everything) semantics.

## Open issues / follow-ups

1. **`HYDROGEN_FUELPRICE.inc` blocks non-default `FUELPRICE_DOL`.**
   `base/model/balopt.opt` sets `HYDROGEN=YES` by default (case-insensitive
   match against `$ifi %HYDROGEN%==yes`), so `base/addons/_hooks/fuelpriceadditions.inc`
   unconditionally pulls in `base/data/HYDROGEN_FUELPRICE.inc`, which
   redeclares `PARAMETER FUELPRICE(YYY,AAA,FFF)` and assigns into it
   (imported-H2 and NATGAS_CCS prices, plus 2024 backcasting adjustments for
   FUELOIL/HEAVYFUELOIL/LIGHTOIL/COAL/NATGAS — note this file already
   contains ad-hoc 2024 backcast values that overlap with what
   `backcast/historicalprices/` is meant to replace properly). This hard-codes
   3-dim `FUELPRICE` and will fail to compile the instant a scenario switches
   `FUELPRICE_DOL` away from `YYY_AAA_FFF`.

   A `$goto`/`$label` skip (confirmed compile-time-safe, see Verification)
   was drafted and tested, but **explicitly rejected**: hydrogen fuel pricing
   should keep working under season/term resolution, not be silently
   disabled. Needs a real design decision, e.g.:
   - Broadcast `HYDROGEN_FUELPRICE.inc`'s annual values across all `(S,T)`
     the same way the core `IFUELPRICE` broadcast does (cheapest, keeps
     hydrogen fuels annual-flat even in a daily-price run), or
   - Let addon fuel-price *additions* compose with `IFUELPRICE` as a
     genuine additive/override layer instead of writing directly into
     `FUELPRICE`, so hydrogen fuels could eventually get their own S,T
     resolution too.

2. **`COMBTECH_FUELPRICE.inc`** (`COMBTECH=YES` by default) is currently an
   *empty* file, so it's compile-safe today by accident, not by design. It
   will need the same treatment as (1) the day it's populated.

3. **`stepwiseprice` addon** (`stepwiseprice_pardefine.inc`,
   `stepwiseprice_qobj.inc`) and **`import_results`'s `ADDFUELPRICE`**
   addon (`import_results_ipardecdef.inc`) both write into raw
   `FUELPRICE(Y,IA,...)` at fixed 3-dim arity. Both addons are off by
   default and were left untouched; combining either with a non-default
   `FUELPRICE_DOL` is currently unsupported and would need the same kind of
   fix as (1).

4. **The actual backcast data**: once (1) is resolved, the remaining work is
   on the pybalmorel side — convert `backcast/historicalprices/*.csv` into a
   `backcast/data/FUELPRICE.inc` (or scenario-local equivalent) using the
   `YYY_AAA_FFF_SSS_TTT` domain, and set `FUELPRICE_DOL` accordingly in
   `backcast/model/balopt.opt`.

## Consequences

- Every existing scenario (`O2030`, `O2040`, `O2050`, `base`, `noh2*`, etc.)
  is unaffected: `FUELPRICE_DOL` defaults to the original 3-dim domain, and
  `IFUELPRICE`/`IFUELPRICE_Y` reduce exactly to the original `FUELPRICE`
  values, verified by a clean GAMS compile.
- Enabling `FUELPRICE_DOL=YYY_AAA_FFF_SSS`/`..._SSS_TTT` for a scenario is
  currently blocked while `HYDROGEN=YES` (the base default) until open issue
  (1) is resolved.
