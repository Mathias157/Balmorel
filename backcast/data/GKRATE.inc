* Backcast: the base ratings, then the weekly overrides from ENTSO-E (see
* CONTEXT.md and README.md), both written by pybalmorel:
* - GKRATE_ENTSOE.inc (nuclear-availability): nuclear availability, replacing
*   the flat 1-GDPLANMAINT/8760 that base gives nuclear.
* - GKRATE_THERMAL_ENTSOE.inc (thermal-availability): thermal availability of
*   the fossil, biomass and waste technologies, from ENTSO-E installed
*   capacity and outages. It leaves nuclear alone.
* Without them, the base ratings stay.
$include '../../base/data/GKRATE.inc';
$if EXIST '../data/GKRATE_ENTSOE.inc' $INCLUDE '../data/GKRATE_ENTSOE.inc';
$if EXIST '../data/GKRATE_THERMAL_ENTSOE.inc' $INCLUDE '../data/GKRATE_THERMAL_ENTSOE.inc';
