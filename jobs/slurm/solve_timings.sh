#!/bin/sh
# Per-solve timing breakdown of a Balmorel job log (rolling, fullyear, ...).
#
# Usage (from scripts/Balmorel/):
#   ./jobs/slurm/solve_timings.sh logs/GREAT_rolling_2050_wy_<jobid>.out [more logs...]
#
# For every CPLEX call prints:
#   gen     - GAMS wall time since the previous solve returned (post-solve bookkeeping + model
#             generation; for solve 1, everything since the job started)
#   barrier - CPLEX barrier time (0 if barrier was not the method that finished)
#   cplex   - total CPLEX time (barrier + crossover + simplex cleanup)
#   status  - GAMS LP status code (1 optimal, 5 optimal with unscaled infeasibilities, ...)
# followed by totals in hours and a count per status. Written for comparing CPLEX option files
# on the same scenario - see jobs/slurm/submit_cplex_test.sh.
set -eu

for log in "$@"; do
    echo "== $log"
    awk '
    function hms(s,  a) { split(s, a, ":"); return a[1] * 3600 + a[2] * 60 + a[3] }
    function elapsed(line) { match(line, /elapsed [0-9:.]+/); return hms(substr(line, RSTART + 8, RLENGTH - 8)) }
    /--- Executing CPLEX/     { n++; gen = elapsed($0) - prev; bar = 0; tot = 0 }
    /^Barrier time =/         { if (!bar) bar = $4 }
    /^Total time on/          { tot = $(NF - 3) }
    /--- LP status/           { st = $4; gsub(/[():]/, "", st); count[st]++
                                printf "%3d  gen=%6.0fs  barrier=%6.0fs  cplex=%7.0fs  status=%s\n", n, gen, bar, tot, st
                                G += gen; B += bar; C += tot }
    /--- Executing after solve/ { prev = elapsed($0) }
    /Job Balmorel.gms Stop/   { match($0, /elapsed [0-9:.]+/); total = substr($0, RSTART + 8, RLENGTH - 8) }
    END {
        printf "TOTAL  solves=%d  gen=%.1fh  barrier=%.1fh  cplex=%.1fh  (non-barrier cplex=%.1fh)  job elapsed=%s\n", n, G / 3600, B / 3600, C / 3600, (C - B) / 3600, total
        for (s in count) printf "  status %s: %d\n", s, count[s]
    }' "$log"
done
