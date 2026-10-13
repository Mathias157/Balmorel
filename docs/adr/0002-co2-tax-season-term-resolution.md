---
status: accepted
---

# 2. Season/term (S,T) resolution for the CO2 tax

Backcasts need a daily-varying CO2 tax, set from the EUA price. `EMI_POL(YYY,CCCRRRAAA,GROUP,EMIPOLSET)` also holds the emission limits, so we can't give it extra dimensions the way ADR 0001 did for `FUELPRICE`. Instead, a new global `TAX_CO2_DOL` (`YYY_CCC` default | `YYY_CCC_SSS_TTT`) switches on an optional parameter `TAX_CO2_ST(YYY,CCCRRRAAA,SSS,TTT)`, read from `TAX_CO2_ST.inc`. Every live CO2-tax term has two `$ifi` branches: the core objective (`Balmorelbb4.inc`), the CCS credit (`CCS_qobj.inc`) and `GENERATION_CO2_TAX` in `OUTPUT_SUMMARY.inc`. The default branch is the original code, unchanged. The S/T branch reads `TAX_CO2_ST` inside the (S,T) sum.

## Consequences

- **Under S/T, `TAX_CO2_ST` replaces `EMI_POL(...,'TAX_CO2')` completely.** Any annual value in `EMI_POL` is ignored, and the tax applies to every area in the country with no `GROUP` dimension. The data only ever sets `ALL_SECTORS`, and every area belongs to it, so this matches the annual behaviour. The model aborts if S/T is selected but `TAX_CO2_ST` is empty after the inactive-year zero-out.
- In the annual branch, the tax **adds up across every GROUP an area belongs to**. Every area is in `ALL_SECTORS` and also in one of the other groups. The S/T branch counts the tax once per country. The 2024 override line in `EMI_POL_APS.inc` (`EMI_POL('2024',CCCRRRAAA,GROUP,'TAX_CO2')=…`) sets every group, so annual 2024 backcasts were taxed twice: about 102 instead of about 50 money/t. This was found while checking this ADR (2026-10-13).
- There is no internal `ITAX_CO2(Y,C,S,T)` copied out to every hour: the default branch keeps the cheap form, with the annual value multiplied outside the sum.
- A scenario whose `balopt.opt` predates this option gets `YYY_CCC` from a fallback in `bb4datainc.inc`.
- In BB4 the HYDROGEN addon's steam-reforming CO2 cost (`addons/hydrogen/hydrogen_qobj.inc`, using `ITAX_CO2_Y`) only applies in BB1–3. `bb4/hydrogen_qobj.inc` has no CO2 tax term, so it needs no change. The `inputout`/`econ` diagnostic printouts (`M_POL`, `ITAX_CO2_Y`) are also BB1–3 only.

## Considered Options

- **Fold CO2 into `IFUELPRICE`** (fuel price + emission factor × EUA): rejected because emissions are per generator (`IM_CO2(G)`) rather than per fuel, and because CCS units remove CO2.
- **Keep `GROUP` in the new parameter**: rejected because it multiplies the size of the parameter for a dimension that has only one value in practice.
- **Always fill an internal `ITAX_CO2(Y,C,S,T)`** (as `IFUELPRICE` does): rejected because it adds a dense parameter to every scenario for no gain when the tax is annual.
