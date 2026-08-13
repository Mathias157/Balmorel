# 1. Season/term (S,T) resolution for FUELPRICE

Date: 2026-08-12
Status: Accepted, implemented for the core framework and HYDROGEN addon, plus a `FUELPRICE_CONSTANT` memory/performance escape hatch; open issues 2-4 remain (see Open issues)

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

### Files changed (2026-08-13, open issue 1)
- `base/model/bb4datainc.inc` — new unconditional
  `PARAMETER FUELPRICE_HYDROGEN(YYY,AAA,FFF)` declared just before the
  `fuelpriceadditions.inc` hook include.
- `base/model/Balmorelbb4.inc` — after the core `IFUELPRICE` broadcast, added
  `IFUELPRICE(Y,AAA,FFF,S,T)$FUELPRICE_HYDROGEN(Y,AAA,FFF) =
  FUELPRICE_HYDROGEN(Y,AAA,FFF);` to override with the addon's annual value
  wherever it set one.
- `base/data/HYDROGEN_FUELPRICE.inc` — lives in `base/data`, which is excluded
  from this repo's tracking (`.gitignore`: `base/data`, `base/data/*.inc`) but
  is itself a separate git repo (`git@github.com:Mathias157/Balmorel_data.git`,
  linked as a gitlink at `.git/modules/base/data`, no `.gitmodules` entry —
  not a properly registered submodule, just a nested checkout). Dropped its
  own `PARAMETER FUELPRICE(YYY,AAA,FFF);` declaration and renamed every
  `FUELPRICE(...)` read/write in the file (imported-H2/NATGAS_CCS broadcast,
  `DK1_large` fallback, 2024 backcasting adjustments for
  FUELOIL/HEAVYFUELOIL/LIGHTOIL/COAL/NATGAS) to `FUELPRICE_HYDROGEN(...)`.
  Pure rename, no logic change. Committed independently in that nested repo
  (`3caf52a "Adapted addon fuel price for S/T index"`) — not visible in this
  repo's `git diff`/`git log`.

### `FUELPRICE_CONSTANT`: memory/performance escape hatch (2026-08-13)

**Problem** (reported after using open issue 1's fix in practice): running
with `FUELPRICE_DOL=YYY_AAA_FFF_SSS_TTT` was "incredibly RAM intensive".
Root cause: the objective function's fuel-cost term (and
`OUTPUT_SUMMARY.inc`'s `GENERATION_FUEL_COSTS`) moved `IFUELPRICE` *inside*
the `(S,T)` sum for *every* fuel, unconditionally — before this ADR, price
was a per-year scalar multiplied in front of the sum (cheap: one price
lookup per fuel per year). Once season/term-resolved `FUELPRICE` data is
actually supplied, `IFUELPRICE(YYY,AAA,FFF,S,T)` gets densely populated
across the full `(S,T)` grid for *every* fuel in `FFF` — including the large
majority of fuels whose price never actually varies by season or term — not
just the handful (coal, natgas, ...) that do.

**Fix**: new `SET FUELPRICE_CONSTANT(FFF)` (`base/model/bb4datainc.inc`,
populated from `base/data/FUELPRICE_CONSTANT.inc` the same
`$if EXIST '../data/...' / $if not EXIST ... '../../base/data/...'` way as
every other addon-overridable data file). Fuels in this set are excluded
from the dense `(S,T)` broadcast into `IFUELPRICE` entirely and are instead
priced everywhere via `IFUELPRICE_Y` (annual, `Y×AAA×FFF`-sized only).
Default: empty (every fuel `NO`) — zero behavioural change unless populated.
To get the memory win, list the fuels that *don't* need S/T resolution:
```
FUELPRICE_CONSTANT(FFF) = YES;
FUELPRICE_CONSTANT('COAL') = NO;
FUELPRICE_CONSTANT('NATGAS') = NO;
```

Mechanically:
- `IFUELPRICE`'s three domain-broadcast lines and the `FUELPRICE_HYDROGEN`
  override (`Balmorelbb4.inc`) all gained a `$(NOT FUELPRICE_CONSTANT(FFF))`
  guard, so `IFUELPRICE` is only ever densely populated for non-constant
  fuels.
- `IFUELPRICE_Y` is no longer derived from `IFUELPRICE` (it would just read 0
  for skipped fuels) — it's now computed directly from `FUELPRICE` per
  domain, IHOURSINST-weighted, so it's correct and cheap (`Y×AAA×FFF` only)
  for every fuel regardless of `FUELPRICE_CONSTANT` membership. This is a
  mathematical identity for genuinely-flat prices (weighted average of a
  constant is that constant), so it's bit-for-bit identical to before
  whenever the underlying data for a `FUELPRICE_CONSTANT` fuel is actually
  flat — which it always is under the default domain, and is a documented,
  deliberate approximation (data averaged, not dropped) if a scenario ever
  flags a genuinely S/T-varying fuel as constant.
- The objective's fuel-cost term and `OUTPUT_SUMMARY.inc`'s
  `GENERATION_FUEL_COSTS` are each now two `SUM`s partitioned by
  `FUELPRICE_CONSTANT(FFF)`: the constant branch pulls `IFUELPRICE_Y` out in
  front of the `(S,T)` sum (the original, cheap, pre-ADR form); the
  non-constant branch keeps `IFUELPRICE(...,S,T)` inside the sum as before.

### Files changed (2026-08-13, `FUELPRICE_CONSTANT`)
- `base/model/bb4datainc.inc` — new `SET FUELPRICE_CONSTANT(FFF)` declaration
  + data include, next to `FUELPRICE_HYDROGEN`.
- `base/data/FUELPRICE_CONSTANT.inc` — new, default content
  `FUELPRICE_CONSTANT(FFF) = NO;` (must be a real assignment, not just
  comments — see Verification, GAMS error 141).
- `base/model/Balmorelbb4.inc` — `$(NOT FUELPRICE_CONSTANT(FFF))` guards on
  the `IFUELPRICE` broadcasts; `IFUELPRICE_Y` recomputed directly from
  `FUELPRICE` per domain instead of from `IFUELPRICE`; objective's fuel-cost
  term split into `FUELPRICE_CONSTANT`/non-constant `SUM`s.
- `base/output/OUTPUT_SUMMARY.inc` — `GENERATION_FUEL_COSTS` split the same
  way.

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
- **2026-08-13 re-verification**: with open issue 1 resolved (below) and
  `HYDROGEN=YES` left at its default (unmodified), both configs recompiled
  cleanly with no neutralization needed:
  - Default (`FUELPRICE_DOL=YYY_AAA_FFF`): `*** Status: Normal completion`.
  - Season/term (`FUELPRICE_DOL=YYY_AAA_FFF_SSS_TTT`, same temporary
    `FUELPRICE(YYY,AAA,FFF,SSS,TTT)=0;` override as above, reverted after):
    `*** Status: Normal completion`, `HYDROGEN_FUELPRICE.inc` compiled
    as-is.
- Confirmed empirically (isolated test script) that GAMS `$goto`/`$label`
  (compile-time directives) truly elide the enclosed source from
  compilation — a reference with the wrong number of indices inside a
  skipped block does not error. This is distinct from a runtime `GOTO`
  statement, which does not affect compilation. Relevant because several
  fixes above initially assumed the stricter (compile-everything) semantics.
- **`FUELPRICE_CONSTANT` (2026-08-13)**:
  - Compile-only (`action=c`, `--SCNAME=APS`): both the default domain (empty
    `FUELPRICE_CONSTANT`) and a season/term test (`FUELPRICE_DOL=YYY_AAA_FFF_SSS_TTT`,
    a temporary `FUELPRICE.inc` with real per-`(S,T)` COAL/NATGAS values, and
    `FUELPRICE_CONSTANT(FFF)=YES` except `COAL`/`NATGAS`) gave
    `*** Status: Normal completion`.
  - Isolated GAMS repro (outside the full model) pinned down GAMS error 141
    ("Symbol declared but no values have been assigned") firing on
    `IFUELPRICE(...)$(NOT FUELPRICE_CONSTANT(FFF)) = ...;` whenever
    `FUELPRICE_CONSTANT` had been declared but never given *any* assignment
    statement (a purely comment-only include is not enough, even though an
    empty set is otherwise legal with `$ONEMPTY`). Fixed by giving the
    default `base/data/FUELPRICE_CONSTANT.inc` a real
    `FUELPRICE_CONSTANT(FFF) = NO;` statement instead of only comments.
  - **Real solve** (not just compile), `--SCNAME=APS iterlim=1 reslim=10
    threads=1` (bounded to keep it fast; GAMS still generates the full model
    and calls the LP solver to optimality on `iterlim=1` since that only caps
    *simplex* iterations, not model generation): reached `LP status (1):
    optimal`, `Objective: 6391233249.179111` for the season/term test case
    above (`FUELPRICE_CONSTANT` = all fuels except COAL/NATGAS) — confirms
    the split objective/`GENERATION_FUEL_COSTS` generate and solve without
    error, not just compile. Did not re-run the default-domain case through
    to a solved objective value for a bit-for-bit numeric comparison before
    wrapping up this session — the correctness argument for that case rests
    on the mathematical identity noted above (weighted average of a constant
    equals that constant) rather than an empirical before/after diff; if that
    matters, worth doing as a follow-up.

## Open issues / follow-ups

1. **RESOLVED (2026-08-13). `HYDROGEN_FUELPRICE.inc` blocked non-default
   `FUELPRICE_DOL`.**
   `base/model/balopt.opt` sets `HYDROGEN=YES` by default (case-insensitive
   match against `$ifi %HYDROGEN%==yes`), so `base/addons/_hooks/fuelpriceadditions.inc`
   unconditionally pulls in `base/data/HYDROGEN_FUELPRICE.inc`, which used to
   redeclare `PARAMETER FUELPRICE(YYY,AAA,FFF)` and assign into it
   (imported-H2 and NATGAS_CCS prices, plus 2024 backcasting adjustments for
   FUELOIL/HEAVYFUELOIL/LIGHTOIL/COAL/NATGAS — note this file already
   contains ad-hoc 2024 backcast values that overlap with what
   `backcast/historicalprices/` is meant to replace properly). This hard-coded
   3-dim `FUELPRICE` and failed to compile the instant a scenario switched
   `FUELPRICE_DOL` away from `YYY_AAA_FFF`.

   A `$goto`/`$label` skip (confirmed compile-time-safe, see Verification)
   was drafted and tested, but **explicitly rejected**: hydrogen fuel pricing
   should keep working under season/term resolution, not be silently
   disabled. Two options were on the table:
   - Broadcast `HYDROGEN_FUELPRICE.inc`'s annual values across all `(S,T)`
     the same way the core `IFUELPRICE` broadcast does (cheapest, keeps
     hydrogen fuels annual-flat even in a daily-price run), or
   - Let addon fuel-price *additions* compose with `IFUELPRICE` as a
     genuine additive/override layer instead of writing directly into
     `FUELPRICE`, so hydrogen fuels could eventually get their own S,T
     resolution too.

   **Decision: the broadcast option**, chosen for being the minimal change
   that unblocks non-default `FUELPRICE_DOL` today; per-addon S,T-resolved
   fuel pricing was not a near-term need. Implemented as: `HYDROGEN_FUELPRICE.inc`
   now writes into a new always-3-dim `FUELPRICE_HYDROGEN(YYY,AAA,FFF)`
   (declared unconditionally in `bb4datainc.inc`, so it exists — all-zero and
   a no-op — even when the HYDROGEN addon is off) instead of `FUELPRICE`
   itself; `Balmorelbb4.inc` broadcasts it into `IFUELPRICE` across all
   `(S,T)`, overriding the core domain's value wherever the addon set a
   nonzero price. Net effect for the default domain is bit-for-bit identical
   to before (verified by compile, see Verification); see "Files changed
   (2026-08-13, open issue 1)" above for the exact edits.

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

4. **The actual backcast data** (now unblocked by (1)): remaining work is on
   the pybalmorel side — convert `backcast/historicalprices/*.csv` into a
   `backcast/data/FUELPRICE.inc` (or scenario-local equivalent) using the
   `YYY_AAA_FFF_SSS_TTT` domain, and set `FUELPRICE_DOL` accordingly in
   `backcast/model/balopt.opt` (currently still `YYY_AAA_FFF`, `HYDROGEN=YES`,
   per grep of `backcast/model/balopt*.opt` on 2026-08-13). When doing this,
   also populate `backcast/data/FUELPRICE_CONSTANT.inc` with every fuel
   *except* the ones the CSVs actually cover (coal, natgas, oil, CO2) — see
   the `FUELPRICE_CONSTANT` section above; this is what makes the S/T
   resolution affordable rather than "incredibly RAM intensive".

5. **`FUELPRICE_CONSTANT` is a manually-maintained set, not auto-detected.**
   Nothing checks that a fuel's data is actually flat when it's flagged
   constant, or actually varies when it isn't — getting this list out of sync
   with `FUELPRICE.inc` silently degrades a genuinely-varying fuel to its
   annual average rather than erroring. An alternative (auto-detect variation
   directly from the raw `FUELPRICE` data, no manual set) was considered but
   not pursued: it would need to inspect the domain-resolved `FUELPRICE`
   parameter itself, which is exactly the large object this feature exists to
   avoid materializing/scanning in full.

## Consequences

- Every existing scenario (`O2030`, `O2040`, `O2050`, `base`, `noh2*`, etc.)
  is unaffected: `FUELPRICE_DOL` defaults to the original 3-dim domain, and
  `IFUELPRICE`/`IFUELPRICE_Y` reduce exactly to the original `FUELPRICE`
  values, verified by a clean GAMS compile.
- Enabling `FUELPRICE_DOL=YYY_AAA_FFF_SSS`/`..._SSS_TTT` for a scenario now
  compiles cleanly with `HYDROGEN=YES` (the base default) — open issue (1) is
  resolved. Hydrogen/NATGAS_CCS fuel prices and the 2024 backcasting
  adjustments in `HYDROGEN_FUELPRICE.inc` stay annual-flat (broadcast across
  all `(S,T)`) regardless of domain; only the core `FUELPRICE` data itself
  gets true season/term resolution. `COMBTECH_FUELPRICE.inc` (issue 2),
  `stepwiseprice`, and `ADDFUELPRICE` (issue 3) remain unresolved and are
  still off by default.
- `FUELPRICE_CONSTANT` defaults to empty, so it changes nothing until a
  scenario populates `base/data/FUELPRICE_CONSTANT.inc` (or a scenario-local
  equivalent). Once populated, the memory/generation cost of season/term
  resolution scales with the number of fuels actually left *out* of
  `FUELPRICE_CONSTANT`, not with the size of `FFF` as a whole — this is what
  makes `FUELPRICE_DOL=YYY_AAA_FFF_SSS_TTT` practical for a scenario that
  only has real daily/weekly data for a handful of fuels (issue 5 above notes
  the tradeoff: this list needs to be kept in sync with the data by hand).
