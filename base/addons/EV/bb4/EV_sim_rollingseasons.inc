*Fixing values relevant for next iteration
VEV_BE_BEV.FX(IY411,IR,IS3LOOPSET+1,T)$(IHASBEV(IR)  AND ORD(T) EQ CARD(T) )=IEV_BEV_available(IY411, IS3LOOPSET,T, IR)*(EV_BEV_batsize(IY411)- 0.01)/1.1;
VEV_BE_BEV.FX(IY411,IR,IS3LOOPSET+1,T)$(IHASBEV(IR)  AND ORD(T) EQ 1 )=IEV_BEV_available(IY411, IS3LOOPSET,T, IR)*(EV_BEV_batsize(IY411)- 0.01)/1.1;

*Boundary SOC for the first and last season, so EVs cannot start the year full or end it drained.
*Pinned to the same availability-derived level as above, NOT to EV_BE_BEV: import_results zeroes
*that parameter when ADDEVSTOS=none (import_results_ipardecdef.inc), which pinned these points to
*an empty fleet and pushed QEV_BEV_BEBALANCE onto the EV_infeas slack.
*S01/T001 and S01/T168 use the S01,T168 level rather than S01,T001, since availability in the very
*first hour of the year is the whole fleet and is not representative.
VEV_BE_BEV.FX(IY411,IR,'S01','T001')$(IHASBEV(IR)) = IEV_BEV_available(IY411,'S01','T168',IR)*(EV_BEV_batsize(IY411)- 0.01)/1.1;
VEV_BE_BEV.FX(IY411,IR,'S01','T168')$(IHASBEV(IR)) = IEV_BEV_available(IY411,'S01','T168',IR)*(EV_BEV_batsize(IY411)- 0.01)/1.1;
VEV_BE_BEV.FX(IY411,IR,'S02','T001')$(IHASBEV(IR)) = IEV_BEV_available(IY411,'S01','T168',IR)*(EV_BEV_batsize(IY411)- 0.01)/1.1;
*S52/T168 uses its OWN availability, not S51's: EV_BEV_return_profile spikes to ~0.71 in the final
*hour of the year (vs ~0.003 at T168 of every other week), so almost the whole fleet plugs in and
*returns its trip energy there. Pinning that hour to the previous week's level leaves ~1.8 TWh of
*return energy with nowhere to go and makes QEV_BEV_BEBALANCE(S52,T168) infeasible.
VEV_BE_BEV.FX(IY411,IR,'S52','T168')$(IHASBEV(IR)) = IEV_BEV_available(IY411,'S52','T168',IR)*(EV_BEV_batsize(IY411)- 0.01)/1.1;

