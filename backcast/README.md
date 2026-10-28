# Backcast scenario

A Balmorel run of a past year with historical inputs, validated against
ENTSO-E data (see `CONTEXT.md` for the terms). The current backcast year is
**2023**. This file records how every year-specific input in `data/` was made,
so the inputs can be regenerated for another year.

All commands run from the repository root in the pixi environment
(`pixi run python -m pybalmorel.backcasting --help`).

## Inputs for 2023

| Input | Files in `data/` | How |
|---|---|---|
| Weather year | `WND_VAR_T`, `WNDFLH`, `SOLE_VAR_T`, `SOLEFLH`, `DE_VAR_T`, `DH*`, `INDIVUSERS_DH*`, `WTRRRVAR_T`, `WTRRSVAR_S` | `cd backcast/weatheryear && python run_weatheryear.py 2023` (config `weatheryear_2023.yml`). The script ends with pybalmorel's `write_scenario_data`, which writes these files and the hydro ones below straight into `data/` from `output/2023/to_balmorel/CapDev/raw`, overwriting them. It also adds `WND_VAR_T.inc`'s fallback lines for areas without their own profile. Don't edit those files by hand, since the next run overwrites them. |
| Electricity demand profile | `DE_VAR_T_ENTSOE.inc` (included at the end of `DE_VAR_T.inc`) | `pixi run python backcast/entsoe_demand_profile.py 2023`, after every weather-year run. **Stopgap:** the weather-year `DE_VAR_T.inc` profiles are corrupt from 2022 onwards (`classic_demand.csv`: LV and LT negative almost every hour, negative hours in the UK, ES, IT and BE, spikes of 20–60× the median in NL, EE and SK, which made NL demand peak at 136 GW). The script overrides `OTHER` and `RESE` with the hourly ENTSO-E actual load on the Backcast Calendar (bidding zones summed, DE4-* taking DE), interpolating hours outside 0.2–3× the median. A region with more than 2% such hours keeps base's profile: AL, BA and IE (IE_SEM is missing S13–S22) in 2023. The UK has no ENTSO-E load and keeps its weather-year profile with 70 hours interpolated. `run_weatheryear.py` overwrites `DE_VAR_T.inc` and with it the `$include`, which the script adds back. Handover: `../pybalmorel/docs/handover-backcast-validation-categories-and-demand.md`. |
| Demand level | `DE.inc`, `DE_ENTSOE.inc` | **Not yet generated.** `python -m pybalmorel.backcasting demand-level backcast backcast/entsoedata 2023` will write `DE_ENTSOE.inc`, as specified in `../pybalmorel/docs/handover-backcast-demand-level.md`. The file holds `DE` for the backcast year: the region's ENTSO-E load × (1 − `DISLOSS_E`), less the electricity Eurostat reports for heating (households' space and water heating, plus electric boilers and heat pumps in district heating). Balmorel adds its own electric heating on top, so its load misses ENTSO-E's only by the electric-heating error and transmission losses. That keeps electric heating a validation metric. Literal Eurostat final consumption less heating (`--basis eurostat`) fits worse per country, 280 against 165 TWh summed absolute gap: ENTSO-E's load covers 7% less than Eurostat in DE and 16% more in PL. `DE.inc` is hand-written. It includes base's `DE.inc` and then `DE_ENTSOE.inc`, if it exists. Without that file, base's patchwork stays (see Known limitations). |
| Hydro inflow level | `WTRRSFLH.inc`, `WTRRRFLH.inc` | Made with the weather year above, in the absolute mode set by `hydro_flh` in `weatheryear_2023.yml` (pybalmorel ADR 0011): the full-load hours are the CorRES 2023 inflow ÷ this scenario's 2023 `GKFX`. The earlier relative mode multiplied base's placeholder full-load hours (4000 h for AT and CH, 3300 h for IT, in both reservoir and run-of-river), which made hydro far too high. Run-of-river inflow above the area's run-of-river capacity moves to its reservoir (PT, and all of ES's, which has no run-of-river `GKFX`). Countries whose CorRES inflow fails the plausibility check get the hydro inflow fallback instead: against Eurostat that is DE, FI, SE and LV (duplicated series, see `docs/handover-corres-hydro-inflow.md`), CH, IT, UK and AT (level; AT at −21% against a ±20% limit). So do the countries CorRES covers only partly (GR, HR, RS) or not at all (17 countries, TR the largest at 31.5 GW). Only BG, ES, FR, NO, PT and RO keep CorRES's level. The mode reads `GKFX` and `IGHYRS` from `model/backcast_input_data.gdx` and the base full-load hours from `base/model/base_input_data.gdx`, reusing either file if it exists (see Regenerating the inputs). |
| VRE level | `WNDFLH_ENTSOE.inc`, `SOLEFLH_ENTSOE.inc` (included at the end of `WNDFLH.inc` and `SOLEFLH.inc`) | **Not yet generated.** `python -m pybalmorel.backcasting vre-flh backcast backcast/entsoedata 2023` will write these files and append their `$include`s, as specified in `../pybalmorel/docs/handover-backcast-vre-flh-from-observed.md`. The weather-year full-load hours are scaled per country and kind (solar, onshore, offshore) to ENTSO-E's 2023 output. Without the scaling, DE solar makes 80.2 TWh against 55.8 observed. Rerun after every weather-year run, which overwrites both files. |
| Fuel prices | `FUELPRICE.inc`, `FUELPRICE_CONSTANT.inc` | `python -m pybalmorel.backcasting fuelprices backcast backcast/historicalprices 2023`. NATGAS (TTF) and COAL (Rotterdam) are daily; every other fuel stays annual from `FUELPRICE_APS.inc`. **Manual fix:** the generated `FUELPRICE.inc` leaves out the `$INCLUDE` of `FUELPRICE_%SCNAME%.inc`. Without it, every annual fuel has no price, and nothing aborts. Add the two `$if EXIST ... FUELPRICE_%SCNAME%.inc` lines back at the top after each regeneration. |
| CO2 tax | `TAX_CO2_ST.inc` | `python -m pybalmorel.backcasting co2-tax backcast backcast/historicalprices 2023 --co2-override UNITED_KINGDOM=84.31 --co2-override ALBANIA=0 --co2-override BOSNIA_AND_HERZEGOVINA=0 --co2-override MONTENEGRO=0 --co2-override NORTH_MACEDONIA=0 --co2-override SERBIA=0 --co2-override TURKEY=0` (the reasons are below). |
| Transmission | `XKFX.inc`, `XKFX_ENTSOE.inc`, `XKRATE.inc` | `python -m pybalmorel.backcasting transmission-flow-limit backcast backcast/entsoedata 2023` writes the Observed Flow Limits (`--percentile`, default 99; pybalmorel ADR 0005/0006/0010) as overrides in `XKFX_ENTSOE.inc`, and adds its `$include` to `XKFX.inc` if missing. An `XKFX_ENTSOE.inc` made with the older `transmission-max-flow` command holds Observed Max Flows and must be regenerated. `XKRATE.inc` rates every open line at 1: the limits are flows that actually happened, so the base 0.95 would cut them a second time. `XKFX.inc` was switched to `'2023'` by hand. Its inline observed-flow block holds the 2024 flows relabelled as 2023, a placeholder that `XKFX_ENTSOE.inc` overrides once it exists. Every `XKFX('<year>',…)` in the file must name the backcast year: a leftover year in `XKFX(Y,…)=XKFX('<year>',…)` silently sets the whole table to zero. |
| Nuclear availability | `GKRATE.inc`, `GKRATE_ENTSOE.inc` | `python -m pybalmorel.backcasting nuclear-availability backcast backcast/entsoedata 2023` writes `GKRATE_ENTSOE.inc`. `GKRATE.inc` includes the base ratings and then `GKRATE_ENTSOE.inc`, if it exists. That file rates each nuclear unit per week: the country's highest hourly ENTSO-E nuclear output in that week ÷ its nuclear `GKFX`. Without the file, nuclear keeps the base rating 1 − GDPLANMAINT/8760 = 0.9425, which lets France produce about 505 TWh against 319 TWh observed. A zero rating must be written as `eps`, because Balmorel reads a literal 0 as the default, full capacity. The UK keeps the base rating, since `entsoedata` has no UK file. Weeks after a country's last ENTSO-E data are rated `eps`, as a closure: Germany's series ends on 15 April, so S16–S52. The command reads `GKFX` from `model/backcast_input_data.gdx` and reuses that file if it exists (`--reload-input` rebuilds it), so it must postdate `GKFX.inc`. Requires `GKRATE_DOL` = `AAA_GGG_SSS` in the option files. |
| Thermal availability | `GKRATE.inc`, `GKRATE_THERMAL_ENTSOE.inc` | **Not yet generated.** `python -m pybalmorel.backcasting thermal-availability backcast backcast/entsoedata 2023` will write `GKRATE_THERMAL_ENTSOE.inc`, as specified in `../pybalmorel/docs/handover-backcast-thermal-capacity-and-outages.md`. It needs two more ENTSO-E downloads, installed capacity and outages. The file rates the fossil, biomass and waste technologies per week: ENTSO-E's installed capacity as a share of `GKFX` (at most 1), less the outages reported that week. It leaves nuclear alone. `GKRATE.inc` includes it after `GKRATE_ENTSOE.inc`, if it exists. The ratings are never taken from observed output, because the fossil mix is a validation metric. Today DE has 48.0 GW of coal and lignite `GKFX` against an observed maximum of 31.9 GW. |
| Must-run floor | `MUSTRUN_ZONE.inc`, `MUSTRUN_ZONE_RRR.inc`, `MUSTRUN_GROUP.inc`, `MUSTRUN_GROUP_FFF.inc`, `MUSTRUN_FLOOR.inc` | **Not yet generated.** `python -m pybalmorel.backcasting must-run-floor backcast backcast/entsoedata 2023` will write them, as specified in `../pybalmorel/docs/handover-backcast-must-run-floor.md`. Run it after the thermal availability. Each floor is the lowest observed hourly output of one fuel group (lignite, hard coal, gas, oil, oil shale and peat, biomass, waste) in one zone in one week. Fossil groups get a floor only in weeks with at least 4 hours at or below 40 €/MWh (nominal day-ahead). Biomass and waste get one every week. Balmorel's `MUSTRUN` addon (`base/addons/mustrun`) requires that much output, or pays `MUSTRUN_PENALTY` (default 300 €2016/MWh) per MWh short. The floor fixes the bottom of the fossil mix by construction, about 209 of the observed fossil TWh in 2023. Only the mix above it is evidence. Without the floor, DE never reaches a 0 price (311 observed hours at or below 0), and DE biomass makes 0.6 TWh against 37.4. |
| Capacity corrections | `GKFX.inc` | Hand-written. Includes the base capacities and adds, for 2023, nuclear units that ran that year but are missing from the base 2023 column: Isar 2 and Neckarwestheim 2 (`DE4-S_A`, 2,720 MW) and Emsland (`DE4-W_A`, 1,336 MW), which ran until 15 April 2023, and Olkiluoto 3 (`FinA` 4,364 MW instead of 2,794). Their closures and outages come from the nuclear availability. Every other capacity is unchanged from `base/data`. |
| Year and seasons | `Y.inc`, `S.inc` | Written by `jobs/backcast_fullyear.sh` from its `year`/`seasons` variables. |
| Time-step length | none | `CHRONOHOUR` comes from `base/data/CHRONOHOUR.inc`, which computes it from the selected `T`: 7 for the full-year run (`T_full`, every 7th hour) and 1 for the rolling run (`T001*T168`). `SSIZE` follows from it. Do not add a `data/CHRONOHOUR.inc` here, since it would override the base formula. |

## Model options

The job scripts copy `model/balopt_full.opt` or `model/balopt_roll.opt` to
`model/balopt.opt`. Some of their settings belong with the inputs above:

- `PLANNED_MAINTENANCE` is off in the full-year run. When on, Balmorel
  schedules maintenance itself for unit-commitment technologies with
  `GDPLANMAINT`, and for nuclear that would come on top of the observed
  outages in the nuclear availability. When off, those technologies keep the
  flat base rating 1 − GDPLANMAINT/8760, unless `GKRATE_ENTSOE.inc` replaces
  it.
- `ADDPLANNEDMAINTENANCE` is off in the rolling run. When on, it loads the
  maintenance schedule from `simex/UCONMAINT.gdx`, which only a full-year run
  with `PLANNED_MAINTENANCE` on writes. With that option off, it would read a
  stale schedule left by an earlier run.
- `ADDBACKUPGEN` is on in both runs. It gives every area with electricity
  or heat demand expensive backup capacity (`import_results_backupgen.inc`).
  It used to work only with `import_results`, so the full-year run had no
  backup: 303 of its 439 heat areas were at penalty prices (about 780 TWh
  of unserved heat, mostly in `*_IND-*` and `*_IDVU-*` areas, whose base
  2023 capacity is too small without investment), and the rolling run
  imported hydro, storage and fuel-use levels from that solution.
- `DEMANDRESPONSE` is off in both runs. In the rolling run alone it let
  Balmorel invest in demand-response capacity that the full-year run did
  not have.
- `MUSTRUN` switches itself on in all three opt files when
  `data/MUSTRUN_FLOOR.inc` exists (see Must-run floor). The addon's
  `QMUSTRUN` holds each zone and fuel group at or above its weekly floor in
  every time step of that week. Its slack costs `MUSTRUN_PENALTY`: 300
  €2016/MWh, unless `data/MUSTRUN_PENALTY.inc` sets another value. That is
  above any fuel cost, so the slack should only cover time steps where the
  floor cannot be met, such as back-pressure CHP with no heat to sink. The
  slack is not in MainResults: compare `PRO_YCRAGFST` with the floors before
  reading the fossil mix. So far the addon has been compiled with the
  backcast data but not yet solved.

## Known limitations

- The electricity demand profile is ENTSO-E's total load, which includes
  demand Balmorel models endogenously (heat pumps, electric boilers, EVs).
  Part of their variation is therefore counted twice. Because the profile
  is an input, the load-shape correlation from `statistics` is no longer
  evidence, only the annual level is.
- Until `DE_ENTSOE.inc` exists, the annual electricity demand level (`DE`)
  for 2023 comes unchanged from `base/data`. That is a per-country patchwork
  of sources and years, not one consistent dataset: the European total is
  close to ENTSO-E's, but the per-country gaps to ENTSO-E's load sum to
  217 TWh. Capacities also come from `base/data`, apart from the nuclear
  corrections in `GKFX.inc`.
- Spain has no run-of-river: its `ES_A . GNR_ROR_WTR` line in
  `base/data/GKFX.inc` is commented out. It stays that way; Spain's
  run-of-river inflow goes to its reservoir instead (see Hydro inflow level).
- UK nuclear keeps the base rating (see Nuclear availability above). Another
  source, such as Elexon, would be needed to rate it.
- Romania's nuclear ceiling at the new ratings (10.85 TWh) stays about 3%
  below the observed 11.21 TWh. ENTSO-E reports Cernavoda at up to 1,453 MW,
  above its 1,300 MW net capacity (the `GKFX`) and even its 1,413 MW gross,
  so this is a reporting difference, not a missing unit; `GKFX` is not
  changed.
- The hydro inflow fallback is a stopgap. Once CorRES releases corrected and
  complete inflow series, every country should use them and the fallback
  should be removed. Latvia is in it because CorRES has the same series for
  `LV_Other_DH` (reservoir) and `LV_RigaR` (run-of-river).
- Countries without CorRES inflow (AL, BA, BE, CZ, DK, EE, HU, IE, LT, LU,
  ME, MK, NL, PL, SI, SK, TR) get the fallback at the long-term observed
  level, with no variation for 2023, and keep Balmorel's base profile within
  the year. With base's full-load hours they would have 128.6 TWh, counting
  GR, HR and RS's missing types, 94.5 TWh of it in TR against 64.2 TWh
  observed. TR is commented out of `base/data/C.inc`, so it is not
  simulated.

## CO2 overrides

Every Balmorel country gets the EUA primary-auction price unless it is
overridden. The overrides are flat, nominal €/t; pybalmorel deflates them to
€2016.

| Country | Override | Why |
|---|---|---|
| `UNITED_KINGDOM` | 84.31 | The UK left the EU ETS in 2021. Its generators paid the UK ETS allowance price plus the £18/t Carbon Price Support. Value = (£55.33 + £18) / 0.86979 GBP per EUR. £55.33 is the 2023 average UKA futures price ([CZapp](https://www.czapp.com/analyst-insights/uk-carbon-prices-set-new-record-low-as-demand-ebbs/); LSEG's Year in Review 2023 gives £55.4). 0.86979 is the ECB 2023 annual-average rate (`EXR.A.GBP.EUR.SP00.A`). UKAs traded clearly below EUAs throughout 2023, so the EUA price would overstate UK costs and distort the UK interconnector flows. The UK price is flat for the year, unlike the daily EUA series. |
| `ALBANIA`, `BOSNIA_AND_HERZEGOVINA`, `NORTH_MACEDONIA`, `SERBIA`, `TURKEY` | 0 | No carbon price on power generation in 2023. |
| `MONTENEGRO` | 0 | Montenegro has had a small national ETS since 2020. It was not modelled, so its cost is probably slightly underestimated. |
| `SWITZERLAND`, `NORWAY` | none (EUA) | The Swiss ETS has been linked to the EU ETS since 2020. Norway is part of the EU ETS through the EEA. |

## Regenerating the inputs

The pixi environment uses the local pybalmorel checkout in `../pybalmorel`
(editable, see `pixi.toml`). The order matters because several steps reuse
cached ReadData output:

1. Delete `model/backcast_input_data.gdx` and `model/Balmorelbb4_ReadData.inc`
   whenever `data/` or pybalmorel's ReadData has changed. pybalmorel only
   copies its ReadData files into `model/` if they are missing, and an old
   copy leaves `IGHYRS` empty, which breaks the absolute hydro mode.
2. Make sure `base/model/base_input_data.gdx` is a complete ReadData run of
   base (it supplies the base full-load hours to the hydro step). Base's
   ReadData needs `SCNAME` defined, which `base/model/balopt.opt` leaves
   commented out. A ReadData that fails to compile still leaves a partial
   gdx, which pybalmorel then reuses. That gdx lacks the fill lines in
   `base/data/WTRRSFLH.inc` and `WTRRRFLH.inc`, so areas such as
   `LV_Other_DH` get no absolute line and keep the fill value in the model
   run (NO1_A1's 3,018 h for reservoirs, FinA's 4,819 h for run-of-river).
3. Weather year and hydro: `cd backcast/weatheryear && python run_weatheryear.py 2023`.
   It writes its files into `data/` itself. The first run rebuilds
   `model/backcast_input_data.gdx` (about half an hour). Then `vre-flh`,
   because the weather year overwrites `WNDFLH.inc` and `SOLEFLH.inc`.
4. `transmission-flow-limit`, `nuclear-availability`,
   `thermal-availability`, `must-run-floor` (after `thermal-availability`,
   whose ratings cap the floors), `demand-level` and
   `entsoe_demand_profile.py`, as in the table.
5. Fuel prices and CO2 tax only when their source data changes.

## Running

1. Set `year` (and `seasons`, for a smoke test) at the top of
   `jobs/backcast_fullyear.sh`.
2. `cd backcast && bsub < ../jobs/backcast_fullyear.sh`. A full year
   (`S01*S52`) submits `jobs/backcast_rolling.sh` afterwards, which reads the
   year from `data/Y.inc`.

The full-year run uses `T_full` (24 terms per week, i.e. 7-hour steps), and the
rolling run uses all 168 hourly terms.
