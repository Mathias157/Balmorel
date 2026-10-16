---
status: accepted
---

# 3. Unit-commitment ramping under LP/RMIP is a fleet ramp rate

`QUCRAMPU`/`QUCRAMPD` (`base/addons/unitcommitment/bb4/uc_eqndecdef.inc`) bound the hourly change in fuel use of a unit-commitment technology. In the original MIP form, ramping down is bounded by

`VGF(t-1) - VGF(t) <= GDUCGMIN*VUCD(t) + GDUCRAMPD*VUCON(t)`

(and the same for ramping up with `VUCU` and `VUCON - VUCU`). The `GDUCGMIN*VUCD` term is the "expanded gradient": a unit that shuts down may drop from minimum load to zero within one step.

Backcasts run as RMIP. Then `VUCD` and `VUCU` can be fractional, so the model can shut down 0.1 of a unit and drop output by an extra `0.1*GDUCGMIN` while the rest of the fleet stays near full load. For nuclear (`GDUCGMIN` = 0.4, `GDUCRAMPD` = 0.125/h) one fractional shutdown frees as much as several hours of ramping. Test runs showed French nuclear ramping faster than its data allows in exactly this way. A first fix (commit 35f3cf1a, and 27a3b7c7 on `great_netzero_evinfra`) replaced `VUCON` with the available units. That loosened the bound and left the expanded-gradient terms in place, so it didn't stop the effect.

We decided that when `SOLVETYPE` is anything other than `MIP`, the bound is a pure ramp rate on available capacity:

`VGF(t-1) - VGF(t) <= GDUCRAMPD * available capacity`

Under `MIP` the original formulation is kept unchanged.

## Consequences

- Under LP/RMIP, start-ups and shutdowns still move the minimum-load floor (`GDUCGMIN*VUCON`) and still cost start-up costs, but they cannot move output faster than the ramp rate.
- A fleet sitting at minimum load cannot shut down completely within one step when `GDUCGMIN > GDUCRAMPD*CHRONOHOUR`; it has to take several steps. That is acceptable for a relaxation and realistic for nuclear.
- The equation is only generated when `CHRONOHOUR*GDUCRAMP < 1`. With nuclear's 0.125/h, it still binds at 6-hour time steps (0.75 per step), so aggregated full-year runs were also affected before this change, though only by at most the remaining 25% per step.
- The same change is handed over to the `great_netzero_evinfra` branch (`docs/handover-uc-ramping-relaxation.md`).

## Considered Options

- **Keep the available-capacity bound but keep the expanded gradient** (35f3cf1a / 27a3b7c7): rejected because it is a relaxation of the original bound and leaves the fractional start/stop route open.
- **Replace `GDUCGMIN` by `min(GDUCGMIN, GDUCRAMP)` in the expanded gradient** (the bound stays proportional to committed units): rejected because it breaks start-up and shutdown whenever `GDUCGMIN > GDUCRAMP*CHRONOHOUR`. Ramping up from a fleet that is fully off gives `VGF <= GDUCRAMPU*VUCON`, while minimum load requires `VGF >= GDUCGMIN*VUCON`, so a fleet that is off can never start again. Ramping down, a fleet at minimum load can only shrink geometrically (nuclear: `VUCON` falls by at most about 31% per hour), so it never reaches zero. The available-capacity bound makes both linear in time. The trade-off is that the chosen bound is looser than the MIP when few units are committed, since it uses all available capacity regardless of commitment.
- **Apply the fleet ramp rate under MIP as well**: rejected because with integer commitment the original formulation is correct, and the capacity bound would let offline units add ramp capability.
