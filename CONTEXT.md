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
what was available or given that year (nuclear and thermal outages, the
usable interconnector capacity, the VRE and demand levels, output that ran
regardless of price), not what the model should decide. Results that a
calibration input fixes by construction are not evidence in backcast
validation.
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

**VRE level**:
The annual output a country's wind or solar fleet could deliver in the
backcast year: the weather year's full-load hours, scaled per country and
kind (solar, onshore, offshore) so that it equals ENTSO-E's reported output
for that year. The hourly profile still comes from the weather year. Written
as `WNDFLH`/`SOLEFLH` overrides. A calibration input.
_Avoid_: Capacity factor (that describes output after curtailment)

**Thermal availability**:
The share of a country's fossil, biomass or waste `GKFX` of one fuel group
that could run in a given week of the backcast year: ENTSO-E's installed
capacity as a share of `GKFX` (at most 1), less the capacity ENTSO-E reports
as out of service that week. Taken from ENTSO-E's installed capacity and
outage reports, never from observed output, because the fossil mix is a
validation metric. Written as weekly `GKRATE` overrides to
`GKRATE_THERMAL_ENTSOE.inc`. A calibration input.
_Avoid_: Capacity factor (that describes output); Nuclear availability (that
is taken from observed output)

**Must-run floor**:
The lowest electricity output a zone's fossil, biomass or waste fuel group
kept in a week of the backcast year when it would have paid to stop: the
week's lowest observed hourly output (ENTSO-E), for weeks in which the
zone's day-ahead price stayed at or below 40 €/MWh for at least 4 hours, and
for biomass and waste in every week. Balmorel must produce at least that
much in every time step of the week, or pay a penalty per MWh short. It
fixes only the bottom of the fossil mix by construction; the fossil mix
above the floor stays a validation metric. Written to `MUSTRUN_FLOOR.inc`,
whose existence switches Balmorel's `MUSTRUN` addon on. A calibration input.
_Avoid_: Minimum load (a property of one unit); Must-run (a plant flag, not
an observed level)

**Validation metric**:
A result the model must reproduce on its own to pass backcast validation:
prices, cross-border flows, the fossil mix above the must-run floor,
electric heating, and the timing of nuclear and hydro output within the
year. Never derived from the same data as a
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

**Demand level**:
The annual exogenous electricity demand (`DE`) of a region in the backcast
year: its ENTSO-E load over the backcast calendar, net of Balmorel's
distribution losses, less the electricity Eurostat reports for heating
(household space and water heating, electric boilers and heat pumps in
district heating), which Balmorel adds endogenously. Taken from ENTSO-E's
load rather than Eurostat's final consumption because the two differ in
coverage (DE: ENTSO-E sees 7% less). With it, Balmorel's load misses
ENTSO-E's only by its electric-heating error and transmission losses.
Written as `DE` overrides to `DE_ENTSOE.inc`. A calibration input; electric
heating stays a validation metric.
_Avoid_: Final consumption (Eurostat's figure, with different coverage);
Demand (ambiguous)

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
