* WeekDecoupled add-on (docs/adr/0006): the reservoir ends the week at its starting level,
* so the week's hydro generation is at most the week's inflow
   + (VHYRS_S(IY411,IA,S) - VHYRS_S(IY411,IA,S++1))
