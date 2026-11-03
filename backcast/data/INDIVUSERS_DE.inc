* Backcast: the INDIVUSERS addon's DE adjustment, then the demand level again.
* base's INDIVUSERS_DE.inc subtracts its estimate of individual electric heating
* (DE1_INDIVHEATING) from RESE and OTHER. It runs in the deadditions hook, after
* DE.inc has applied DE_ENTSOE.inc. The demand level in DE_ENTSOE.inc is already
* net of the electricity Balmorel adds endogenously for heat, so it is re-applied
* here, and DE_ENTSOE.inc's DE is the one Balmorel solves with. INDIVUSERS is the
* last DE adjustment in base/addons/_hooks/deadditions.inc (after TRANSPORT and
* INDUSTRY). Without DE_ENTSOE.inc this is base's adjustment alone.
$include '../../base/data/INDIVUSERS_DE.inc';
$if EXIST '../data/DE_ENTSOE.inc' $INCLUDE '../data/DE_ENTSOE.inc';
