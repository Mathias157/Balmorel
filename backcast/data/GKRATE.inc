* Backcast: the base ratings, then the weekly nuclear availability from ENTSO-E
* (see CONTEXT.md and README.md). GKRATE_ENTSOE.inc is written by pybalmorel
* and replaces the flat 1-GDPLANMAINT/8760 that base gives nuclear. Without
* it, the base ratings stay.
$include '../../base/data/GKRATE.inc';
$if EXIST '../data/GKRATE_ENTSOE.inc' $INCLUDE '../data/GKRATE_ENTSOE.inc';
