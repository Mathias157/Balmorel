* Backcast: the base annual electricity demand, then the demand level for the
* backcast year (see CONTEXT.md and README.md). DE_ENTSOE.inc is written by
* pybalmorel (demand-level): ENTSO-E load less transmission losses, net of
* distribution losses, less the electric heating Balmorel adds endogenously
* (the previous run's, ADR 0015, or Eurostat's in a new year's first run).
* Without it, the base demand stays (2020 Eurostat final consumption for the
* countries added later, older sources for the rest). The INDUSTRY and
* INDIVUSERS addons adjust DE again after this file; INDUSTRY_DE.inc and
* INDIVUSERS_DE.inc in this folder re-apply DE_ENTSOE.inc after them.
$include '../../base/data/DE.inc';
$if EXIST '../data/DE_ENTSOE.inc' $INCLUDE '../data/DE_ENTSOE.inc';
