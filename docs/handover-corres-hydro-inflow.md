# Handover to CorRES: errors in the hydro inflow series

For the CorRES development team. Found on 2026-10-21 while calibrating hydro
for the Balmorel 2023 backcast.

## Data checked

`weatheryear_inputs_2023/hydro_data/res_inflow.csv` (reservoir inflow) and
`ror_inflow.csv` (run-of-river inflow). Both are hourly, 1980-01-01 to
2023-12-31, one column per Balmorel area. The same errors are in the older
1980–2021 release (`mbrpdoc-great/data/weatheryear_inputs/hydro_data/`).

Annual energy below is the sum of the hourly values / 1e6. That assumes the
values are average MW per hour, which gives TWh. Please confirm the unit.
Observed values are Eurostat `nrg_bal_c`, `PPRD`, `RA100` (hydro without
pumped storage), mean 2013–2022, except where noted. `nrg_bal_peh` `RA100`
gives the same values except for the UK, where it includes pumped output.

## Errors

**1. Reservoir and run-of-river columns are identical.** For `DE4-E_A`,
`DE4-N_A`, `DE4-S_A`, `DE4-W_A`, `FinA`, `SE1A`, `SE2A`, `SE3A` and `SE4A`,
the two files hold the same series hour by hour. Anyone who adds the two
types together counts these areas twice:

| Country | Reservoir + RoR, mean 1980–2023 (TWh/yr) | Observed natural-inflow hydro (TWh/yr) |
|---|---|---|
| SE (SE1–SE4) | 68.2 + 68.2 = 136 | 67.1 |
| FI | 13.5 + 13.5 = 27 | 14.5 |

**2. All German sub-areas carry the same series.** The four DE4 areas are
identical to each other in both files. Each one has 13.45 TWh/yr, which is
roughly Germany's national total. Germany therefore gets 4 × 2 × 13.45 ≈
108 TWh/yr, against 19.6 TWh observed. The national series looks like it
was copied to each sub-area instead of split between them.

**2b. Latvia is in two areas at once.** `LV_Other_DH` in
`res_inflow.csv` and `LV_RigaR` in `ror_inflow.csv` are identical hour by hour
over 1980–2023, 2.87 TWh/yr each, so Latvia gets 5.7 TWh/yr against 2.6
TWh observed. Most Latvian hydro is the Daugava cascade, so one of the two
columns is probably a copy.

**3. Switzerland is far too low, with the wrong split.** CH has 12.3 TWh/yr
reservoir and 1.9 TWh/yr run-of-river, so 14 TWh/yr in total. Observed Swiss
hydro excluding pumping is ~35–37 TWh/yr (Swiss Federal Office of Energy;
Eurostat has no CH), of which run-of-river is ~16–17 TWh/yr.

**4. Too low:**

| Country | Reservoir + RoR, mean 1980–2023 (TWh/yr) | Observed (TWh/yr) | Difference |
|---|---|---|---|
| UK | 0 + 3.5 = 3.5 | 5.6 (2013–2019) | −38% |
| IT | 5.5 + 26.3 = 31.8 | 45.2 | −30% |
| AT | 4.7 + 26.4 = 31.1 | 39.2 | −21% |

The UK has only a run-of-river column; Scottish reservoir hydro seems to be
missing.

Plausible at country level (within ±20%): BG, ES, FR, NO, PT, RO, and RS's
run-of-river column alone (9.1 against 10.0 TWh/yr).

**5. Missing countries and types.** These have hydro capacity in Balmorel but
no column in either file: AL, BA, BE, CZ, DK, EE, HU, IE, LT, LU, ME, MK, NL,
PL, SI, SK and TR, by far the largest being TR (64.2 TWh/yr observed), then
AL (6.5), BA (5.5), SI (4.5) and SK (4.2). GR and HR have a reservoir column
but no run-of-river one, and RS the reverse. Please say whether the GR, HR
and RS columns hold the whole country's inflow or one type only.

## How to reproduce

```python
import pandas as pd
r = pd.read_csv("res_inflow.csv", index_col=0, parse_dates=True)
o = pd.read_csv("ror_inflow.csv", index_col=0, parse_dates=True)
annual = lambda df: df.groupby(df.index.year).sum().mean() / 1e6  # TWh/yr
print(pd.DataFrame({"res": annual(r), "ror": annual(o)}))
print([c for c in r if c in o and (r[c] - o[c]).abs().max() < 1e-9])  # identical res/ror
```

## Effect on Balmorel today

Balmorel weather-year runs only use the relative factor (each year's inflow ÷
the 1980–2023 mean, in `*_inflow_flh_fac.csv`). The absolute level comes from
Balmorel's own full-load hours, so the errors above only show up once the
absolute inflow is used, which the backcast is about to start doing. In the
meantime, the backcast falls back to observed long-term generation for
countries that fail the check above or are missing. This fallback is temporary. Once
corrected CorRES inflow series are released, the backcast will use them for
every country and the fallback will be removed.
