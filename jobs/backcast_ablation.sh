#!/bin/sh
### General options
### -- specify queue --
#BSUB -q hpc
### -- set the job Name (overridden by the submit script) --
#BSUB -J backcast_ablation
### -- ask for number of cores (default: 1) --
#BSUB -n 10
### -- specify that the cores must be on the same host --
#BSUB -R "span[hosts=1]"
### -- specify that we need 10GB of memory per core/slot --
#BSUB -R "rusage[mem=10GB]"
### -- specify that we want the job to get killed if it exceeds 10 GB per core/slot --
#BSUB -M 10GB
### -- set walltime limit: hh:mm --
#BSUB -W 24:00
### -- send notification at completion --
#BSUB -N
### -- Specify the output and error file. %J is the job-id --
#BSUB -o ../logs/backcast_ablation_%J.out
#BSUB -e ../logs/backcast_ablation_%J.err

# One leave-one-out ablation of the backcast full-year run. Don't submit this
# directly: jobs/submit_backcast_ablations.sh makes the scenario folder (a copy
# of backcast/ with one development removed) and submits this from inside it.
# The run name comes from the folder name, e.g. backcast_abl_hydro_F2023.

name=$(basename "$PWD")
year=$(grep -oE '^[0-9]{4}' data/Y.inc)

cd model
gams Balmorel threads=$LSB_DJOB_NUMPROC --USEOPTIONFILE=2 --SCNAME=APS --scenario_name="${name}_F${year}" 2>&1 | tee ../gams.log
cd ..

# The full-year run is a single solve
count=$(grep -c 'LP status (1): optimal' gams.log || true)
if [ "$count" -eq 1 ]; then
  echo "OPTIMAL: ${name} had ${count} optimal solution"
else
  echo "NOT OPTIMAL: ${name} had ${count} optimal solutions, expected 1"
  exit 1
fi
