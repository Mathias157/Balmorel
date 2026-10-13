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

**Observed load**:
Electricity demand as actually measured, taken from ENTSO-E. It is the
reference that a backcast is validated against.
_Avoid_: Demand (ambiguous)

**Modelled demand**:
The electricity demand profile produced by CorRES for a weather year and used
as Balmorel input. Comparing it with observed load is part of backcast
validation.
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
