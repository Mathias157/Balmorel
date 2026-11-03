* Backcast: the INDUSTRY addon's DE adjustment, then the demand level again.
* base's INDUSTRY_DE.inc subtracts its estimate of industrial process heat
* (DE1_IND) from PII. It runs in the deadditions hook, after DE.inc has applied
* DE_ENTSOE.inc. The demand level in DE_ENTSOE.inc is already net of the
* electricity Balmorel adds endogenously for heat, so it is re-applied here. The
* same happens in INDIVUSERS_DE.inc, so DE_ENTSOE.inc's DE is the one Balmorel
* solves with whichever of the two addons is on. Without DE_ENTSOE.inc this is
* base's adjustment alone.
$include '../../base/data/INDUSTRY_DE.inc';
$if EXIST '../data/DE_ENTSOE.inc' $INCLUDE '../data/DE_ENTSOE.inc';
