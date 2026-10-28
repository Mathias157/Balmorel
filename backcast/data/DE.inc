* Backcast: the base annual electricity demand, then the demand level for the
* backcast year (see CONTEXT.md and README.md). DE_ENTSOE.inc is written by
* pybalmorel (demand-level): ENTSO-E load net of distribution losses, less
* Eurostat's electricity for heating, which Balmorel adds endogenously.
* Without it, the base demand stays (2020 Eurostat final consumption for the
* countries added later, older sources for the rest).
$include '../../base/data/DE.inc';
$if EXIST '../data/DE_ENTSOE.inc' $INCLUDE '../data/DE_ENTSOE.inc';
