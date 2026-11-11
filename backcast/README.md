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
| Electricity demand profile | `DE_VAR_T_ENTSOE.inc` (included at the end of `DE_VAR_T.inc`) | `python -m pybalmorel.backcasting demand-profile backcast backcast/entsoedata 2023 --reload-input`, after every weather-year run. It replaces the stopgap `backcast/entsoe_demand_profile.py`. It overrides `OTHER` and `RESE` with the hourly ENTSO-E actual load on the Backcast Calendar (bidding zones summed, DE4-* taking DE), interpolating hours outside 0.2–3× the median. A region without ENTSO-E load, or with more than 2% such hours, takes its input-data (weather-year) profile, cleaned the same way. Failing that, it keeps its current profile. In 2023 that is the UK, CY, LU, MT and TR (no usable ENTSO-E load of their own; the UK's is the weather-year profile), and AL and BA, whose ENTSO-E load fails the check. IE uses Ireland's control-area load (`entsoedata/2023_IE_load.csv`), not the `IE_SEM` bidding zone, which is all-island (Northern Ireland is in Balmorel's UK) and also misses S13–S22. The demand level uses the same control-area load. `run_weatheryear.py` overwrites `DE_VAR_T.inc` and with it the `$include`, which the command adds back. Run it with `--reload-input` *before* adding the include back: the cached input GDX holds the old weather-year profile, and once the include is back, ReadData reads the old file's UK profile. `classic_demand.csv` was corrupt from 2022 onwards (LV and LT negative almost every hour, and NL, EE and the UK uncorrelated with the real load) and was fixed on 2026-11-03. With the fix, 25 of its 29 regions pass the weather-year plausibility check (`drop_implausible_demand`). DE4-* fail because the file gives all four the same profile, so they keep base's `DE_VAR_T` in `DE_VAR_T.inc`, under the ENTSO-E override. In the backcast only the UK profile changes. Handover: `../pybalmorel/docs/handover-backcast-validation-categories-and-demand.md`. |
| Demand level | `DE.inc`, `DE_ENTSOE.inc`, `INDUSTRY_DE.inc`, `INDIVUSERS_DE.inc` | `python -m pybalmorel.backcasting demand-level backcast backcast/entsoedata 2023` writes `DE_ENTSOE.inc` (pybalmorel ADR 0015). The file holds `DE` for the backcast year: the region's ENTSO-E load less what the previous run added on top of `DE`, × (1 − `DISLOSS_E`). That is its transmission losses, the electricity it used for heat (`ENDOGENOUS_ELECT2HEAT`), and its distribution losses on anything but exogenous demand: those on that heating, and the 1–2% of wind and solar output that Balmorel books as distribution loss (`DISLOSS_E_AG`, 6.7 TWh in the compared countries). Balmorel adds all three back on top, so its load is ENTSO-E's as long as they stay as they were. It doesn't, quite (E2H falls by about 0.3 TWh per TWh of `DE`), so the level is iterated (see Iterating the demand level). It reads the previous run from `backcastoutput/balmorel_load.csv`, which `format` writes, and needs a full-year hourly run (`backcast_R2023`, not the 7-hour `backcast_F2023`). The first run of a new year takes `--heat eurostat` instead: the load × (1 − `DISLOSS_E`), less the electricity Eurostat reports for heating (households' space and water heating, plus electric boilers and heat pumps in district heating), as specified in `../pybalmorel/docs/handover-backcast-demand-level.md` (variant (a′)). Eurostat's heating has a narrower scope than Balmorel's (IT 10.1 against 59.6 TWh of E2H in `backcast_R2023` of 2026-10-29), which is why the model's own heating replaced it. The `DE_ENTSOE.inc` of 2026-11-10 was (a′), and the rerun with it is iteration 0. The `DE_ENTSOE.inc` of 2026-11-11 is iteration 1 (`--heat model`, from that rerun). CH is written under `--heat model`, with no Eurostat coverage check (Eurostat has no Swiss balances). Literal Eurostat final consumption less heating (`--basis eurostat`) fits worse per country, 280 against 165 TWh summed absolute gap: ENTSO-E's load covers 7% less than Eurostat in DE and 16% more in PL. The ENTSO-E load is its mean over the Backcast Calendar times 8760 hours, since Balmorel spreads `DE` over 8760 hours whatever its time steps cover; until 2026-11-10 it was summed over the calendar's 8736 hours, which left `DE` 0.27% low (6.9 TWh in 2023). `DE.inc` is hand-written. It includes base's `DE.inc` and then `DE_ENTSOE.inc`, if it exists. `INDUSTRY_DE.inc` and `INDIVUSERS_DE.inc` are hand-written too. They include base's file of the same name (the INDUSTRY and INDIVUSERS addons' `DE` adjustments, which subtract their own heat estimates from `PII`, `RESE` and `OTHER` after `DE.inc`) and then `DE_ENTSOE.inc` again, so its `DE` is final. Without them, `backcast_R2023` subtracted heat twice: 509 TWh more on top of the 238 TWh already netted, which made its load 369 TWh low. `demand-level` warns if a wrapper is missing or doesn't re-apply `DE_ENTSOE.inc`. |
| Hydro inflow level | `WTRRSFLH.inc`, `WTRRRFLH.inc` | Made with the weather year above, in the absolute mode set by `hydro_flh` in `weatheryear_2023.yml` (pybalmorel ADR 0011): the full-load hours are the CorRES 2023 inflow ÷ this scenario's 2023 `GKFX`. The earlier relative mode multiplied base's placeholder full-load hours (4000 h for AT and CH, 3300 h for IT, in both reservoir and run-of-river), which made hydro far too high. Run-of-river inflow above the area's run-of-river capacity moves to its reservoir (PT, and all of ES's, which has no run-of-river `GKFX`). Countries whose CorRES inflow fails the plausibility check get the hydro inflow fallback instead: against Eurostat that is DE, FI, SE and LV (duplicated series, see `docs/handover-corres-hydro-inflow.md`), CH, IT, UK and AT (level; AT at −21% against a ±20% limit). So do the countries CorRES covers only partly (GR, HR, RS) or not at all (17 countries, TR the largest at 31.5 GW). Only BG, ES, FR, NO, PT and RO keep CorRES's level. The mode reads `GKFX` and `IGHYRS` from `model/backcast_input_data.gdx` and the base full-load hours from `base/model/base_input_data.gdx`, reusing either file if it exists (see Regenerating the inputs). |
| VRE level | `WNDFLH_ENTSOE.inc`, `SOLEFLH_ENTSOE.inc` (included at the end of `WNDFLH.inc` and `SOLEFLH.inc`) | `python -m pybalmorel.backcasting vre-flh backcast backcast/entsoedata 2023` writes these files and appends their `$include`s, as specified in `../pybalmorel/docs/handover-backcast-vre-flh-from-observed.md`. The weather-year full-load hours are scaled per country and kind (solar, onshore, offshore) to ENTSO-E's 2023 output. Without the scaling, DE solar makes 80.2 TWh against 55.8 observed. Rerun after every weather-year run, which overwrites both files. |
| Fuel prices | `FUELPRICE.inc`, `FUELPRICE_CONSTANT.inc` | `python -m pybalmorel.backcasting fuelprices backcast backcast/historicalprices 2023`. NATGAS (TTF) and COAL (Rotterdam) are daily; every other fuel stays annual from `FUELPRICE_APS.inc`. **Manual fix:** the generated `FUELPRICE.inc` leaves out the `$INCLUDE` of `FUELPRICE_%SCNAME%.inc`. Without it, every annual fuel has no price, and nothing aborts. Add the two `$if EXIST ... FUELPRICE_%SCNAME%.inc` lines back at the top after each regeneration. |
| CO2 tax | `TAX_CO2_ST.inc` | `python -m pybalmorel.backcasting co2-tax backcast backcast/historicalprices 2023 --co2-override UNITED_KINGDOM=84.31 --co2-override ALBANIA=0 --co2-override BOSNIA_AND_HERZEGOVINA=0 --co2-override MONTENEGRO=0 --co2-override NORTH_MACEDONIA=0 --co2-override SERBIA=0 --co2-override TURKEY=0` (the reasons are below). |
| Transmission | `XKFX.inc`, `XKFX_ENTSOE.inc`, `XKRATE.inc` | `python -m pybalmorel.backcasting transmission-flow-limit backcast backcast/entsoedata 2023` writes the Observed Flow Limits (`--percentile`, default 99; pybalmorel ADR 0005/0006/0010) as overrides in `XKFX_ENTSOE.inc`, and adds its `$include` to `XKFX.inc` if missing. An `XKFX_ENTSOE.inc` made with the older `transmission-max-flow` command holds Observed Max Flows and must be regenerated. `XKRATE.inc` rates every open line at 1: the limits are flows that actually happened, so the base 0.95 would cut them a second time. `XKFX.inc` was switched to `'2023'` by hand. Its base table had FR–IE at 700 MW each way, the Celtic Interconnector, which is not in service until about 2027; Balmorel sent 4.6 TWh from FR to IE over it in `backcast_R2023`. It was removed on 2026-11-10. ENTSO-E has no data for FR–IE, so no override corrected it. CY–GR went the same day: 1,000 MW each way in the base table, the Great Sea Interconnector, which is not built; it carried 3.8 TWh GR→CY in `backcast_R2023`, and CY has no ENTSO-E data, so CY now runs isolated on its own plants. The other table borders without an override are AL–MK, AL–RS (Kosovo), and LU's borders with DE4-W and FR (inside `DE_LU`). Its inline observed-flow block holds the 2024 flows relabelled as 2023, a placeholder that `XKFX_ENTSOE.inc` overrides once it exists. Every `XKFX('<year>',…)` in the file must name the backcast year: a leftover year in `XKFX(Y,…)=XKFX('<year>',…)` silently sets the whole table to zero. |
| Nuclear availability | `GKRATE.inc`, `GKRATE_ENTSOE.inc` | `python -m pybalmorel.backcasting nuclear-availability backcast backcast/entsoedata 2023` writes `GKRATE_ENTSOE.inc` (pybalmorel ADR 0013). `GKRATE.inc` includes the base ratings and then `GKRATE_ENTSOE.inc`, if it exists. That file rates each nuclear unit per week: the country's highest hourly ENTSO-E nuclear output in that week ÷ its nuclear `GKFX`. Without the file, nuclear keeps the base rating 1 − GDPLANMAINT/8760 = 0.9425, which lets France produce about 505 TWh against 319 TWh observed. A zero rating must be written as `eps`, because Balmorel reads a literal 0 as the default, full capacity. The UK keeps the base rating, since `entsoedata` has no UK file. Weeks after a country's last ENTSO-E data are rated `eps`, as a closure: Germany's series ends on 15 April, so S16–S52. The command reads `GKFX` from `model/backcast_input_data.gdx` and reuses that file if it exists (`--reload-input` rebuilds it), so it must postdate `GKFX.inc`. Requires `GKRATE_DOL` = `AAA_GGG_SSS` in the option files. |
| Thermal availability | `GKRATE.inc`, `GKRATE_THERMAL_ENTSOE.inc` | `python -m pybalmorel.backcasting thermal-availability backcast backcast/entsoedata 2023` writes `GKRATE_THERMAL_ENTSOE.inc` (pybalmorel ADR 0014). It needs two ENTSO-E downloads besides generation: installed capacity and outages (unavailability of generation units). The file rates the fossil, biomass and waste technologies per country, fuel group and week: ENTSO-E's installed capacity as a share of `GKFX` (at most 1), less the share of it reported out of service that week, averaged over the week. Planned and forced outages both count, each event at its latest revision, without cancelled or withdrawn events. It leaves nuclear alone. `GKRATE.inc` includes it after `GKRATE_ENTSOE.inc`, if it exists. The ratings are never taken from observed output, because the fossil mix is a validation metric. Without them, DE has 48.0 GW of coal and lignite `GKFX` against an observed maximum of 31.9 GW. `backcastoutput/thermal_capacity.csv` compares `GKFX`, installed capacity and observed output per country and group, and `thermal_availability.csv` holds the weekly ratings. Countries without ENTSO-E installed capacity keep their base `GKRATE`: IT, SE1–4, UK, TR, CH, BA, CY, LU, ME, MT and XK. AL, HR, MK, NO1–5 and SI have no outage reports, so they only get the capacity share. Exact duplicate rows in the outage download (10,495 of 69,492 in 2023) count once; the runs made before that fix counted them twice (see Known limitations). Like the nuclear command, it reads `model/backcast_input_data.gdx` and reuses it if it exists. |
| Must-run floor | `MUSTRUN_ZONE.inc`, `MUSTRUN_ZONE_RRR.inc`, `MUSTRUN_GROUP.inc`, `MUSTRUN_GROUP_FFF.inc`, `MUSTRUN_FLOOR.inc` | `python -m pybalmorel.backcasting must-run-floor backcast backcast/entsoedata 2023` writes them (ADR 0005). Run it after the thermal availability, because each floor is capped at the zone's `GKFX` × `GKRATE`. Each floor is the lowest observed hourly output of one fuel group (lignite, hard coal, gas, oil, oil shale and peat, biomass, waste) in one zone in one week. Fossil groups get a floor only in weeks with at least 4 hours at or below 40 €/MWh (nominal day-ahead). Biomass and waste get one every week. Balmorel's `MUSTRUN` addon (`base/addons/mustrun`) requires that much output, or pays `MUSTRUN_PENALTY` (default 300 €2016/MWh) per MWh short. The floor fixes the bottom of the fossil mix by construction, about 209 of the observed fossil TWh in 2023. Only the mix above it is evidence. In the runs before the floor, DE never reached a 0 price (311 observed hours at or below 0), and DE biomass made 0.6 TWh against 37.4. In the `mustrun` ablation of `backcast_F2023`, dropping the floor lowers biomass by 33 TWh and raises gas by 13 TWh. |
| Capacity corrections | `GKFX.inc` | Hand-written. Includes the base capacities and adds, for 2023, nuclear units that ran that year but are missing from the base 2023 column: Isar 2 and Neckarwestheim 2 (`DE4-S_A`, 2,720 MW) and Emsland (`DE4-W_A`, 1,336 MW), which ran until 15 April 2023, and Olkiluoto 3 (`FinA` 4,364 MW instead of 2,794). Their closures and outages come from the nuclear availability. It also multiplies CH's 2023 solar PV by 1,000: `base/data/GKFX_renewable.inc` holds Switzerland's PV in GW where Balmorel reads MW (1.91 … 5.84 for 2017–2023), so base has 5.84 MW against about 6 GW built. Base itself is unchanged. Every other capacity is unchanged from `base/data`. |
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
  reading the fossil mix. The addon is part of the solved `backcast_F2023`
  run: the `mustrun` ablation, which drops it, differs from `ref`, and
  `ref` matches `backcast_F2023` byte for byte.

## Known limitations

- The electricity demand profile is ENTSO-E's total load, which includes
  demand Balmorel models endogenously (heat pumps, electric boilers, EVs).
  Part of their variation is therefore counted twice. Because the profile
  is an input, the load-shape correlation from `statistics` is no longer
  evidence, only the annual level is.
- The demand level in the `DE_ENTSOE.inc` of 2026-11-10 left out
  Eurostat's electricity for heating (`--heat eurostat`). Balmorel's
  endogenous electric heating covers more than that (industrial process
  heat, services), so each country's load gap in the runs made with it is
  its heating-scope difference: IT, DE and ES too high. From iteration 1
  on (the `DE_ENTSOE.inc` of 2026-11-11, `--heat model`, see Iterating the demand level) a country's load
  gap is the previous run's residual instead, and its electric heating
  against Eurostat's (`E2H_minus_H_TWh` in `demand_level.csv`) is the
  heat-sector finding. Regions without `DE_ENTSOE.inc` lines (AL, CY, MT,
  TR, UK, and CH until iteration 1) keep base's `DE`, a per-country
  patchwork of sources and years. Capacities come from
  `base/data`, apart from the corrections in `GKFX.inc` (nuclear, CH solar).
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
- `backcast_F2023`, `backcast_R2023` and the ablations were solved with
  thermal ratings that counted some outages twice. The ENTSO-E outage
  download has 10,495 exact duplicate rows out of 69,492 (same event, same
  revision), and `thermal-availability` counted each one until 2026-11-09.
  Summed over countries and averaged over the weeks, the rated capacity was
  193.0 GW, against 198.8 GW since the fix (DE +3.2 GW, mostly hard coal and
  gas). Their thermal output, prices and must-run floors are therefore not
  comparable with runs made after the fix. Their must-run floors were also
  capped at `GKFX` × the base `GKRATE`, not at the weekly thermal rating,
  because the floors had been generated before the ratings reached the
  input GDX. Regenerating them on 2026-11-10 changed 244 of 3,994 floors
  but only 0.08 TWh of the 243.7 TWh they require. It dropped the 34 floors
  that are now rated 0: CZ oil (18 weeks) and SK hard coal (3), where
  ENTSO-E reports almost no installed capacity, and NL biomass (13), where
  the reported outages cover all of it. ENTSO-E nevertheless shows output
  in each of those weeks.
- The runs solved before 2026-11-10 also had `DE` 0.27% low (6.9 TWh
  summed; see Demand level), the FR–IE and CY–GR links (see Transmission)
  and 5.84 MW of CH solar instead of about 6 GW (see Capacity corrections). Their
  load comparison put Balmorel 4.9 TWh below ENTSO-E at system level, but
  only because LU was left out of the Balmorel side while ENTSO-E's `DE_LU`
  load includes it (6.1 TWh); pybalmorel now compares LU inside DE.
  Together, the fixes are expected to move the system-level gap to about
  +8 TWh.
- Thermal outages are averaged over the week, so a group's rated capacity
  can be below its observed peak in that week. DE lignite is rated below its
  observed weekly peak in 9 weeks, by up to 1.2 GW, and Balmorel can't reach
  those hours.
- The thermal capacity share derates a whole fuel group, not the units that
  closed. Where ENTSO-E covers fewer plants than `GKFX`, typically small CHP
  and industrial plants, it is too low: ES waste is rated 0.10 and PL
  biomass 0.19. These plants also produce heat, so the derating reaches the
  heat balance too.
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
   commented out, so build it from `base/model` with
   `gams Balmorel_ReadData.gms --SCNAME=APS gdx=base_input_data.gdx`
   (about 15 minutes, about 550 MB). A ReadData that fails to compile still
   leaves a partial gdx of about 2 MB, with only the tables and an empty
   `GKFX`, which pybalmorel then reuses. The one from 2026-10-28 was like
   that. That gdx lacks the fill lines in
   `base/data/WTRRSFLH.inc` and `WTRRRFLH.inc`, so areas such as
   `LV_Other_DH` get no absolute line and keep the fill value in the model
   run (NO1_A1's 3,018 h for reservoirs, FinA's 4,819 h for run-of-river).
3. Weather year and hydro: `cd backcast/weatheryear && python run_weatheryear.py 2023`.
   It writes its files into `data/` itself. The first run rebuilds
   `model/backcast_input_data.gdx` (about half an hour), before the new
   files are written.
   - Next, `demand-profile ... --reload-input`. That rebuilds the GDX
     from the new files. `DE_VAR_T.inc` doesn't include
     `DE_VAR_T_ENTSOE.inc` at that point, so the regions on the
     weather-year fallback (the UK) get the new profile. The command then
     adds the include back.
   - Then `vre-flh`, because the weather year overwrites `WNDFLH.inc` and
     `SOLEFLH.inc`.
4. `transmission-flow-limit`, `nuclear-availability`,
   `thermal-availability`, `must-run-floor` (after `thermal-availability`,
   whose ratings cap the floors) and `demand-level`, as in the table.
5. Fuel prices and CO2 tax only when their source data changes.

## Running

1. Set `year` (and `seasons`, for a smoke test) at the top of
   `jobs/backcast_fullyear.sh`.
2. `cd backcast && bsub < ../jobs/backcast_fullyear.sh`. A full year
   (`S01*S52`) submits `jobs/backcast_rolling.sh` afterwards, which reads the
   year from `data/Y.inc`.

The full-year run uses `T_full` (24 terms per week, i.e. 7-hour steps), and the
rolling run uses all 168 hourly terms.

### Iterating the demand level

`DE_ENTSOE.inc` leaves out the electricity the previous run used for heat
and the losses it had (see Demand level), and those move
with the level. Each iteration is:

```bash
pixi run sync-mainresults backcast
pixi run python -m pybalmorel.backcasting format backcast_R2023 backcast backcast/entsoedata 2023 --overwrite
pixi run python -m pybalmorel.backcasting demand-level backcast backcast/entsoedata 2023
pixi run sync-up
# on the cluster, from /work3/mberos/Balmorel/backcast:
bsub < ../jobs/backcast_fullyear.sh
```

`demand-level` prints the previous run's residual: what its load missed
ENTSO-E's by, net of distribution losses, summed over Europe and summed in absolute terms over
countries. Iterate for as long as it keeps falling; about 10 TWh summed
over countries is as close as the other errors allow. It warns if
`balmorel_load.csv` is not from the run that solved with the current
`DE_ENTSOE.inc` (more than 1% off in a region), and stops if it is not one
full-year hourly run. For a new backcast year, the first level comes from
`demand-level ... --heat eurostat`, which needs no previous run.

## Ablation runs

`jobs/submit_backcast_ablations.sh` measures what each development adds, by
rerunning the full-year run with one development removed at a time
(leave-one-out). Each ablation gets its own scenario folder,
`backcast_abl_<name>/` at the repository root (gitignored), holding a copy of
`data/` made at submission and its own `simex/`, `output/` and listing. The
ablations therefore don't overwrite each other, or the `simex/` files the
rolling run imports from `backcast_F<year>`. The script header lists what each
ablation removes. `ref` removes nothing and should reproduce
`backcast_F<year>`, which checks the setup.

1. `pixi run sync-up`, then on the cluster, from the repository root:
   `jobs/submit_backcast_ablations.sh` (default: `ref hydro nuclear demand
   mustrun vre`). `thermal` also exists but has not been run. Names can be
   given as arguments.
   `--no-submit` only builds the folders. An existing folder is skipped, so
   delete it to rebuild it.
2. Each job runs `jobs/backcast_ablation.sh` from inside its folder and writes
   `backcast_abl_<name>/model/MainResults_backcast_abl_<name>_F<year>.gdx`.
3. Fetch the results with `mkdir -p backcast_abl_<name>/model && pixi run
   sync-mainresults backcast_abl_<name>`.

The `hydro` ablation restores the relative-mode `WTRRSFLH.inc` and
`WTRRRFLH.inc` from commit `59531c77`, the last one before the absolute mode.
The `nuclear` ablation also drops `GKFX.inc`, since its 2023 nuclear units
only close through the weekly ratings. The full-year run's results cover
every 7th hour only. When comparing them with ENTSO-E, sample ENTSO-E at the
same hours, or use the annual symbols (`PRO_YCRAGF`).
