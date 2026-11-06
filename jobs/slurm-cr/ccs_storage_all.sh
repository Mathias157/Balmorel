#!/bin/bash
### General options
### -- specify partition and account --
#SBATCH --partition=fatnode
#SBATCH --account=dtu_00075
### -- set the job Name --
#SBATCH --job-name=GREAT_ccs_storage_all
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=1
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- memory: CR_CORE does not reserve it, only picks nodes with this much in total --
#SBATCH --mem=16G
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=0-03:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=logs/GREAT_ccs_storage_all_%j.out
#SBATCH --error=logs/GREAT_ccs_storage_all_%j.err

# Re-runs `verify ccs-storage` (GREAT docs/adr/0084) for every F<year>/R<year> MainResults on this
# machine. The check inside rolling_<year>.sh crashed in every job so far: pybalmorel's
# GamsWorkspace ran against the jobs' GAMS 46.5 with gamsapi 54.6 and read EL_PRICE_YCR when
# asked for OBJ_YCR. This job points verify at GAMS 53.5 instead. Report only - it changes no
# result. Read the summary table at the end of the log.
#
# R is the run the check is for: rolling solves one week at a time, so it has no annual storage
# equation. F has QCCS_STORAGE, so its line is the reference that R's captured CO2 should match.
# Year copies (<scenario>_Y<year>) are checked too and tagged, since failed runs stay there - their
# results are not finished results (AGENTS.md). CPXTEST_* copies are skipped.
#
# Second table: net CO2 of R against F, for every folder holding both. R's weekly cap is F's weekly
# net CO2 (EMI_POLNA_S ALL_SECTORS, Balmorelbb4.inc QLIMCO2ROLLS), so a week where R emits more than
# F is a week where R used its CO2 slack, and the sum of those excesses is the slack R needed. Both
# runs report EMI_POLNA_S in tonnes per real week (OUTPUT_SUMMARY.inc resets R's hour weights to a
# full year before writing). For those slack weeks it also gives R's exogenous electricity + heat load
# over F's: a ratio above 1 means F's 12 steps per week under-represent the load R has to serve.
# The load is compared as a mean over each run's own time steps, because F's 12 steps and R's 168
# hours carry different hour weights.
# That reading holds for R runs made since GREAT docs/adr/0089 (2026-10-25). Older R runs capped every
# week at zero net (before 0060) or at a 52 times too small share of F's week (0060), so their excess
# is that cap, not slack. Check the R file's date before reading its line as slack.
#
# Usage, from scripts/Balmorel/:
#   sbatch jobs/slurm-cr/ccs_storage_all.sh
#   sbatch --export=ALL,YEARS="2030 2040 2050" jobs/slurm-cr/ccs_storage_all.sh

cd "${SLURM_SUBMIT_DIR:-$PWD}"
if [ ! -d jobs/slurm-cr ]; then
    echo "ERROR: run from scripts/Balmorel/, not $PWD"
    exit 1
fi

VERIFY_GAMS_DIR="${VERIFY_GAMS_DIR:-/home/projects/dtu_00075/apps/gams/gams53.5_linux_x64_64_sfx}"
if [ ! -x "$VERIFY_GAMS_DIR/gams" ]; then
    echo "ERROR: no GAMS in VERIFY_GAMS_DIR=$VERIFY_GAMS_DIR"
    exit 1
fi
# verify.py reads GAMS_SYSTEM_DIR; without it, GamsWorkspace takes the first gams on PATH
export GAMS_SYSTEM_DIR="$VERIFY_GAMS_DIR"
export PATH="$VERIFY_GAMS_DIR:$PATH"
export LD_LIBRARY_PATH="$VERIFY_GAMS_DIR:${LD_LIBRARY_PATH:-}"

YEARS="${YEARS:-2050}"
echo "ccs-storage check of F/R ${YEARS} results with GAMS $(head -c 40 "$VERIFY_GAMS_DIR/gamsstmp.txt" 2>/dev/null) at $(date)"

summary=$(mktemp)
printf "%s\t%s\t%s\t%s\n" "FOLDER" "SCENARIO" "VERDICT" "RESULT" > "$summary"

for model_dir in */model; do
    folder=${model_dir%/model}
    case "$folder" in CPXTEST_*) continue ;; esac
    tag=""
    case "$folder" in *_Y20[0-9][0-9]) tag=" (Year copy)" ;; esac
    for year in $YEARS; do
        for run in F R; do
            for gdx in "$model_dir"/MainResults_*_${run}${year}.gdx; do
                [ -f "$gdx" ] || continue
                scenario=$(basename "$gdx" .gdx)
                scenario=${scenario#MainResults_}
                echo
                echo "=== ${folder}${tag}: ${scenario}"
                out=$(pixi run verify "$PWD/$folder" ccs-storage --scenario "$scenario" --top 5 2>&1)
                status=$?
                # The limits come from base/data only (no switch touches them), so a folder whose own
                # all_endofmodel.gdx is missing or predates them can use base's
                if [ ! -f "$model_dir/all_endofmodel.gdx" ] || echo "$out" | grep -q 'predates the storage limit'; then
                    echo "(no limits in ${folder}/model/all_endofmodel.gdx - using base/model/all_endofmodel.gdx)"
                    out=$(pixi run verify "$PWD/$folder" ccs-storage --scenario "$scenario" --top 5 \
                        --gdx "$PWD/base/model/all_endofmodel.gdx" 2>&1)
                    status=$?
                fi
                # Drop pixi's cache warnings and the GAMS/gamsapi version warning, keep the rest
                echo "$out" | grep -v -e 'WARN cache' -e 'warn(' -e 'UserWarning' -e 'GamsWorkspace('
                line=$(echo "$out" | grep -E "^${year}: .* Mt captured" | head -1)
                if echo "$out" | grep -q 'ABOVE THE LIMIT'; then verdict=ABOVE
                elif echo "$out" | grep -q 'No CO2 captured'; then verdict=NO_CO2_CAPTURED
                elif echo "$out" | grep -q 'predates the storage limit'; then verdict=NO_LIMIT_IN_GDX
                elif [ $status -eq 0 ] && [ -n "$line" ]; then verdict=OK
                else verdict="ERROR(exit $status)"; line=$(echo "$out" | grep -E 'Error|ERROR' | tail -1)
                fi
                printf "%s\t%s\t%s\t%s\n" "${folder}${tag}" "$scenario" "$verdict" "${line:--}" >> "$summary"
            done
        done
    done
done

echo
echo "=== Summary ($(($(wc -l < "$summary") - 1)) results)"
column -t -s $'\t' "$summary"
rm -f "$summary"

# --- Net CO2: R against F ----------------------------------------------------------------------
gdxd="$VERIFY_GAMS_DIR/gdxdump"
work=$(mktemp -d)
# A week counts as a slack week when R exceeds F by more than this (tonnes)
SLACK_WEEK_TOL="${SLACK_WEEK_TOL:-1000}"

# S,tonnes of net CO2 per week
weekly_net() {
    "$gdxd" "$1" symb=EMI_POLNA_S format=csv |
        awk -F, 'NR>1 { gsub(/"/, ""); if ($3 == "ALL_SECTORS" && $4 == "LIM_CO2") print $2 "," $5 }'
}
# S,mean MW of exogenous electricity + heat load over the run's time steps in that week
weekly_exo_load() {
    {
        "$gdxd" "$1" symb=EL_DEMAND_YCRST format=csv |
            awk -F, 'NR>1 { gsub(/"/, ""); if ($6 == "EXOGENOUS") print $4 "," $5 "," $8 }'
        "$gdxd" "$1" symb=H_DEMAND_YCRAST format=csv |
            awk -F, 'NR>1 { gsub(/"/, ""); if ($7 == "EXOGENOUS") print $5 "," $6 "," $9 }'
    } | awk -F, '{ s[$1] += $3; if (!(($1 "," $2) in seen)) { seen[$1 "," $2] = 1; n[$1]++ } }
                 END { for (k in s) print k "," s[k] / n[k] }'
}

co2_summary=$(mktemp)
printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "FOLDER" "SCENARIO" "F_NET_Mt" "R_NET_Mt" "R-F_Mt" \
    "SLACK_Mt" "SLACK_WEEKS" "LOAD_R/F_IN_SLACK_WEEKS" > "$co2_summary"

for model_dir in */model; do
    folder=${model_dir%/model}
    case "$folder" in CPXTEST_*) continue ;; esac
    tag=""
    case "$folder" in *_Y20[0-9][0-9]) tag=" (Year copy)" ;; esac
    for year in $YEARS; do
        for rgdx in "$model_dir"/MainResults_*_R${year}.gdx; do
            [ -f "$rgdx" ] || continue
            fgdx="${rgdx%_R${year}.gdx}_F${year}.gdx"
            scenario=$(basename "$rgdx" .gdx)
            scenario=${scenario#MainResults_}
            scenario=${scenario%_R${year}}
            echo
            echo "=== Net CO2 ${folder}${tag}: ${scenario} R${year} against F${year}"
            if [ ! -f "$fgdx" ]; then
                echo "no $(basename "$fgdx") in ${folder}/model - skipped"
                printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "${folder}${tag}" "$scenario" "no F" - - - - - >> "$co2_summary"
                continue
            fi
            weekly_net "$fgdx" > "$work/fnet"
            weekly_net "$rgdx" > "$work/rnet"
            weekly_exo_load "$fgdx" > "$work/fload"
            weekly_exo_load "$rgdx" > "$work/rload"
            # Per-week table of the slack weeks (largest first), then one summary line
            awk -F, -v tol="$SLACK_WEEK_TOL" -v out="$work/line" '
                FILENAME ~ /fnet$/  { f[$1] = $2; w[$1] = 1; next }
                FILENAME ~ /rnet$/  { r[$1] = $2; w[$1] = 1; next }
                FILENAME ~ /fload$/ { fl[$1] = $2; next }
                FILENAME ~ /rload$/ { rl[$1] = $2; next }
                END {
                    for (s in w) {
                        ft += f[s]; rt += r[s]; d = r[s] - f[s]
                        if (d > tol) {
                            slack += d; nw++; sfl += fl[s]; srl += rl[s]
                            printf "%s\t%.3f\t%.3f\t%.3f\t%.0f\t%.0f\t%.3f\n", s, f[s] / 1e6, r[s] / 1e6, d / 1e6, fl[s], rl[s], (fl[s] > 0 ? rl[s] / fl[s] : 0)
                        }
                        afl += fl[s]; arl += rl[s]
                    }
                    ratio = (nw > 0 && sfl > 0) ? sprintf("%.3f (all weeks %.3f)", srl / sfl, arl / afl) : sprintf("- (all weeks %.3f)", (afl > 0 ? arl / afl : 0))
                    printf "%.2f\t%.2f\t%.2f\t%.2f\t%d\t%s\n", ft / 1e6, rt / 1e6, (rt - ft) / 1e6, slack / 1e6, nw, ratio > out
                }' "$work/fnet" "$work/rnet" "$work/fload" "$work/rload" |
                LC_ALL=C sort -t $'\t' -k4,4gr > "$work/weeks"
            if [ -s "$work/weeks" ]; then
                echo "Slack weeks (R above F by more than ${SLACK_WEEK_TOL} t), largest first:"
                { printf "S\tF_Mt\tR_Mt\tR-F_Mt\tF_LOAD_MW\tR_LOAD_MW\tR/F\n"; head -15 "$work/weeks"; } | column -t -s $'\t'
            else
                echo "No week where R emits more than F"
            fi
            printf "%s\t%s\t%s\n" "${folder}${tag}" "$scenario" "$(cat "$work/line")" >> "$co2_summary"
        done
    done
done

echo
echo "=== Net CO2 summary, R against F ($(($(wc -l < "$co2_summary") - 1)) pairs; Mt per year, load = exogenous electricity + heat)"
column -t -s $'\t' "$co2_summary"
rm -f "$co2_summary"
rm -rf "$work"
