# Balmorel

Pan-European, sector-coupled energy system model. This glossary currently
covers the backcasting work: validating Balmorel against a historical year.

## Backcasting

**Backcast**:
A Balmorel run of a past year with historical inputs, whose results are
compared against observed ENTSO-E data to validate the model.
_Avoid_: Hindcast, historical run

**Backcast year**:
The single historical calendar year a backcast represents. It is also the
model year `Y` of that run; each backcast year is a separate run.
_Avoid_: Base year, weather year (a different concept)

**Backcast calendar**:
The mapping from a backcast year's real dates to Balmorel's 52 seasons × 168
terms: S01 starts on the year's first Monday, and the days outside the 52 full
weeks are dropped.
_Avoid_: Time index, timeslice mapping

**Backcast preprocessing**:
Turning raw historical data for a backcast year into Balmorel input data.
_Avoid_: Backcast validation (that is the comparison step, after the run)

**Backcast validation**:
Comparing a backcast's results with observed ENTSO-E load, prices and
generation for the same backcast year.
_Avoid_: Backcast preprocessing

**Calibration input**:
A backcast input derived from observed data for the backcast year that says
what was available that year (nuclear outages, the usable interconnector
capacity), not what the model should decide. Results that a calibration
input fixes by construction are not evidence in backcast validation.
_Avoid_: Tuning, fitting

**Observed Flow Limit**:
The usable capacity of one direction of an interconnector in a backcast: the
99th percentile of the observed hourly flow in that direction, over the
hours of the backcast year with flow in that direction. A direction without
flow gets 0. On a border that spans several ENTSO-E zones, it is taken on
the flows summed hour by hour. A calibration input.
_Avoid_: Observed Max Flow (the earlier definition, which an outlier hour
could set), NTC, transmission capacity

**Nuclear availability**:
The share of a country's nuclear capacity that could run in a given week of
the backcast year, taken from the highest observed hourly nuclear output in
that week. It includes outages and maintenance, and closures: weeks after a
country's observed series ends are rated zero. A calibration input.
_Avoid_: Capacity factor, load factor (those describe output, not
availability)

**Natural-inflow hydro**:
Run-of-river and reservoir hydro fed by natural water inflow. It excludes the
output of pumped storage, which is electricity storage.
_Avoid_: Hydro (ambiguous about pumped storage)

**Hydro inflow fallback**:
For a country whose CorRES inflow fails the plausibility check, or that
CorRES covers only partly or not at all, the inflow level comes from observed
long-term natural-inflow hydro generation instead. CorRES still provides that
year's variation where it has data; a country without CorRES data gets none.
It is a stopgap until CorRES fixes and completes its inflow series.
_Avoid_: Hydro calibration (the backcast year's generation is never the
reference)

**Validation metric**:
A result the model must reproduce on its own to pass backcast validation:
prices, cross-border flows, the fossil mix, and the timing of nuclear and
hydro output within the year. Never derived from the same data as a
calibration input.
_Avoid_: Target (ambiguous between the two)

**Observed load**:
Electricity demand as actually measured, taken from ENTSO-E. It includes
whatever EV charging and power-to-heat happened that year. It is the
reference that a backcast is validated against.
_Avoid_: Demand (ambiguous)

**Modelled demand**:
The exogenous electricity demand profile produced by CorRES for a weather year
and used as Balmorel input. It excludes the consumption Balmorel decides
endogenously (power-to-heat, EV charging), so it is not compared with observed
load on its own. Observed load is compared with modelled demand plus that
endogenous consumption, which is how the power-to-heat share is validated.
_Avoid_: Demand (ambiguous), load

**Historical price series**:
An observed market price for a fuel or emission allowance over the backcast
year, at daily resolution, mapped onto the backcast calendar.

**Price year**:
The euro year that every monetary input to Balmorel is expressed in: €2016.
Historical prices are deflated to it before they are used as inputs.
_Avoid_: Base year, EUR2012 (outdated header leftover)

**CO2 tax**:
The cost per tonne of CO2 emitted, as Balmorel models it. In a backcast it is
set from the EUA price.
_Avoid_: CO2 price (ambiguous between the model input and the market price)

**EUA price**:
The observed market price of an EU emission allowance. It is the source data
for the CO2 tax in a backcast.
_Avoid_: CO2 tax (that is the model input)
