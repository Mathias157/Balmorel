* GREAT scenario NPY -- forced new-build nuclear.
*
* Absolute floor on total installed nuclear capacity, summed over ALL countries
* in the model (QKMINFNA, base/model/Balmorelbb4.inc:2013). The constraint reads
*
*     SUM(C, GKFX - VDECOM_EXO_ACCUM + VGKNACCUMNET) =G= FKMINNA(Y,FFF)
*
* i.e. it counts exogenous capacity AND endogenous investments. The value below
* is therefore a TOTAL installed capacity, not a new-build increment.
*
* 150 GW by 2050: target of the European Nuclear Alliance (16 member states) as
* elaborated by nucleareurope, cross-checked against the Commission's PINC high
* case of 144 GW (SWD accompanying COM(2026) 120). Baseline GKFX nuclear in 2050
* is 52.7 GW across the model footprint, so this forces ~97 GW of new build.
*
* No geographical rows and no FKPOT mask: siting is left entirely to the
* optimiser. See docs/adr/0031-forced-nuclear-npy-scenario.md.

TABLE FKMINNA(YYY,FFF)     'Minimum capacity by year and fuel (aggregated countries)(MW)'
                                   NUCLEAR
2050                               150000
;
