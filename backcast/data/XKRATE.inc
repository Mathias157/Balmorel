* Backcast: no transmission derating. XKFX holds Observed Flow Limits, which
* are flows that actually happened (losses are in XLOSS), so the base 0.95
* would cut them a second time. Lines rated eps (closed) stay closed.
$include '../../base/data/XKRATE.inc';
XKRATE(IRRRE,IRRRI,S)$(XKRATE(IRRRE,IRRRI,S) GT 0) = 1;
