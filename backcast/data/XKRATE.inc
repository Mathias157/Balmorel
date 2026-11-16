* Backcast: no transmission derating. XKFX holds Observed Flow Limits, which
* are flows that actually happened (losses are in XLOSS), so the base 0.95
* would cut them a second time. Lines rated eps (closed) stay closed.
$include '../../base/data/XKRATE.inc';
XKRATE(IRRRE,IRRRI,S)$(XKRATE(IRRRE,IRRRI,S) GT 0) = 1;
* Transmission availability: weekly ratings of the directions whose ENTSO-E
* outage reports describe the whole border (pybalmorel transmission-availability)
$if EXIST '../data/XKRATE_ENTSOE.inc' $INCLUDE '../data/XKRATE_ENTSOE.inc';
