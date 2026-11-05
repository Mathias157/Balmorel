#!/bin/bash
# Leave-one-out ablation of the backcast full-year run, for a tornado chart of
# how much each development contributes. Each ablation is its own scenario
# folder, backcast_abl_<name>/, holding a copy of backcast/data (a snapshot at
# submission time) with one development removed. The folders keep their own
# simex/, output/ and listing, so the runs don't overwrite each other or the
# baseline backcast's import files for the rolling run.
#
# Usage, from anywhere in the repository:
#   jobs/submit_backcast_ablations.sh [--no-submit] [ablation ...]
# Without names it builds and submits $default_ablations. --no-submit only
# builds the folders (for a compile check). An existing folder is never
# overwritten: delete it to rebuild it.
#
# Ablations (what is removed, relative to the current backcast):
#   ref      nothing: the current backcast, rerun in the same setup
#   hydro    absolute hydro FLH -> the earlier relative mode, base placeholder
#            FLH x CorRES factor (WTRRSFLH/WTRRRFLH from before eb2a04cb)
#   nuclear  weekly nuclear availability and the 2023 nuclear GKFX
#            corrections (GKRATE_ENTSOE.inc, GKFX.inc) -> flat base rating
#   thermal  weekly thermal availability (GKRATE_THERMAL_ENTSOE.inc)
#   mustrun  must-run floor (MUSTRUN_FLOOR.inc, which switches the addon on)
#   vre      ENTSO-E scaling of wind and solar FLH (WNDFLH/SOLEFLH_ENTSOE.inc
#            replaced by empty files) -> weather-year FLH
#   demand   ENTSO-E demand level and profile (DE_ENTSOE.inc,
#            DE_VAR_T_ENTSOE.inc) -> base DE and weather-year profile
set -eu

year=2023
seasons='S01*S52'
default_ablations="ref hydro nuclear demand mustrun vre"
# Last commit with the relative-mode hydro FLH files
hydro_relative_commit=59531c77

cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

submit=1
if [ "${1:-}" = "--no-submit" ]; then
  submit=0
  shift
fi
ablations=${*:-$default_ablations}

for a in $ablations; do
  case $a in
  ref | hydro | nuclear | thermal | mustrun | vre | demand) ;;
  *)
    echo "Unknown ablation '$a'"
    exit 1
    ;;
  esac
done

mkdir -p logs

for a in $ablations; do
  dir="backcast_abl_${a}"
  if [ -e "$dir" ]; then
    echo "$dir exists, skipping it (delete it to rebuild)"
    continue
  fi

  mkdir -p "$dir/model"
  cp -r backcast/data "$dir/data"
  cp backcast/model/Balmorel.gms backcast/model/cplex.op2 "$dir/model/"
  cp backcast/model/balopt_full.opt "$dir/model/balopt.opt"
  cp backcast/data/T_full.inc "$dir/data/T.inc"
  printf 'SET Y(YYY) "Years in the simulation"\n/\n%s\n/;\n' "$year" >"$dir/data/Y.inc"
  printf 'SET S(SSS) "Seasons in the simulation"\n/\n%s\n/;\n' "$seasons" >"$dir/data/S.inc"

  case $a in
  ref) ;;
  hydro)
    for f in WTRRSFLH WTRRRFLH; do
      git show "${hydro_relative_commit}:backcast/data/${f}.inc" >"$dir/data/${f}.inc"
    done
    ;;
  nuclear) rm "$dir/data/GKRATE_ENTSOE.inc" "$dir/data/GKFX.inc" ;;
  thermal) rm "$dir/data/GKRATE_THERMAL_ENTSOE.inc" ;;
  mustrun) rm "$dir/data/MUSTRUN_FLOOR.inc" ;;
  vre)
    # WNDFLH.inc/SOLEFLH.inc fall back to base's _ENTSOE file if these are
    # missing, which doesn't exist, so leave them empty instead
    for f in WNDFLH_ENTSOE SOLEFLH_ENTSOE; do
      echo "* Ablation: no ENTSO-E scaling of the weather-year FLH" >"$dir/data/${f}.inc"
    done
    ;;
  demand) rm "$dir/data/DE_ENTSOE.inc" "$dir/data/DE_VAR_T_ENTSOE.inc" ;;
  esac
  echo "Built $dir"

  if [ "$submit" -eq 1 ]; then
    (cd "$dir" && bsub -J "$dir" <../jobs/backcast_ablation.sh)
  fi
done
