This is the repository of the pan-European, sector coupled 
Balmorel energy system model.

It is a pixi environment 

## pybalmorel Basics

`analyse.py`'s commands are all built on the `pybalmorel.Balmorel` class. Its
methods differ a lot in cost — know which one a command actually needs:

- `Balmorel(path, gams_system_directory=...)` — just scans `path` for
  scenario folders (dirs containing `model/Balmorel.gms` +
  `model/cplex.op2`/`op4`). No result files touched yet.
- `model.locate_results(suffix_naming_only=True)` — cheap. Indexes each
  scenario's `MainResults*.gdx` *filenames* only, populating
  `model.scenario_names` and the `model.scname_to_scfolder` /
  `scfolder_to_scname` dicts. Does not read any GDX data.
- `model.collect_results(suffix_naming_only=True)` — calls
  `locate_results()`, then eagerly builds `model.results` (a `MainResults`
  object) from the located files. This is the point at which
  `model.results.get_result(symbol)` becomes usable.
- `model.results.get_result(symbol)` — pulls one GAMS symbol (e.g.
  `PRO_YCRAGF`, `OBJ_YCR`) into a DataFrame, one column per index set plus
  `Value`. This is the actual (potentially slow) GDX read; column layout per
  symbol is defined in `pybalmorel/formatting.py`'s
  `balmorel_mainresults_symbol_columns`.

`analyse.py`'s `CLI()` group callback only calls `model.locate_results(...)`
up front, and only for command names in its whitelist (the `command in
[...]` check) — this just builds `ctx.obj["Balmorel"]` cheaply. Any command
that actually needs symbol data must call `model.collect_results(...)`
itself before touching `model.results` (see `scenario_overview`/`net_import`
for the pattern), or go through the module-level `collect_results(symbol)`
helper at the bottom of `analyse.py` (confusingly same name as the
`Balmorel` method it wraps), which additionally pickle-caches each symbol to
`analysis/files/<symbol>.pkl` so repeated CLI invocations skip re-reading
the GDX.

