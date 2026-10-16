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
| Weather year | `WND_VAR_T`, `WNDFLH`, `SOLE_VAR_T`, `SOLEFLH`, `DE_VAR_T`, `DH*`, `INDIVUSERS_DH*`, `WTRR*` | `cd backcast/weatheryear && python run_weatheryear.py 2023` (config `weatheryear_2023.yml`), then copied by hand from `output/2023/to_balmorel/CapDev/raw`. `WND_VAR_T.inc` has hand-added fallback lines at the end for areas without their own profile. |
| Fuel prices | `FUELPRICE.inc`, `FUELPRICE_CONSTANT.inc` | `python -m pybalmorel.backcasting fuelprices backcast backcast/historicalprices 2023`. NATGAS (TTF) and COAL (Rotterdam) are daily; every other fuel stays annual from `FUELPRICE_APS.inc`. **Manual fix:** the generated `FUELPRICE.inc` leaves out the `$INCLUDE` of `FUELPRICE_%SCNAME%.inc`. Without it, every annual fuel has no price, and nothing aborts. Add the two `$if EXIST ... FUELPRICE_%SCNAME%.inc` lines back at the top after each regeneration. |
| CO2 tax | `TAX_CO2_ST.inc` | `python -m pybalmorel.backcasting co2-tax backcast backcast/historicalprices 2023 --co2-override UNITED_KINGDOM=84.31 --co2-override ALBANIA=0 --co2-override BOSNIA_AND_HERZEGOVINA=0 --co2-override MONTENEGRO=0 --co2-override NORTH_MACEDONIA=0 --co2-override SERBIA=0 --co2-override TURKEY=0` (the reasons are below). |
| Transmission | `XKFX.inc`, `XKFX_ENTSOE.inc` | `python -m pybalmorel.backcasting transmission-max-flow backcast backcast/entsoedata 2023` writes the Observed Max Flow overrides (pybalmorel ADR 0005/0006). `XKFX.inc` was switched to `'2023'` by hand. Its inline observed-flow block holds the 2024 flows relabelled as 2023, a placeholder that `XKFX_ENTSOE.inc` overrides once it exists. Every `XKFX('<year>',…)` in the file must name the backcast year: a leftover year in `XKFX(Y,…)=XKFX('<year>',…)` silently sets the whole table to zero. |
| Year and seasons | `Y.inc`, `S.inc` | Written by `jobs/backcast_fullyear.sh` from its `year`/`seasons` variables. |
| Time-step length | none | `CHRONOHOUR` comes from `base/data/CHRONOHOUR.inc`, which computes it from the selected `T`: 7 for the full-year run (`T_full`, every 7th hour) and 1 for the rolling run (`T001*T168`). `SSIZE` follows from it. Do not add a `data/CHRONOHOUR.inc` here, since it would override the base formula. |

Capacities (`GKFX`) and the annual electricity demand level (`DE`) for 2023
come unchanged from `base/data`. This is a known limitation, to be revisited
if validation is far off.

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

## Running

1. Set `year` (and `seasons`, for a smoke test) at the top of
   `jobs/backcast_fullyear.sh`.
2. `cd backcast && bsub < ../jobs/backcast_fullyear.sh`. A full year
   (`S01*S52`) submits `jobs/backcast_rolling.sh` afterwards, which reads the
   year from `data/Y.inc`.

The full-year run uses `T_full` (24 terms per week, i.e. 7-hour steps), and the
rolling run uses all 168 hourly terms.
