#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windq
### -- set the job Name --
#SBATCH --job-name=get_adequacies
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=5
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=0-02:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=logs/get_adequacies_%j.out
#SBATCH --error=logs/get_adequacies_%j.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source jobs/slurm/functions.sh

# Get scenario choice and run name from jobs/scenario_choice.sh
source jobs/scenario_choice.sh

# Make exceptions (e.g.: failed runs or runs not finished)
not_allowed_runs=("APS_base_S8T24MMF1_R2050")

# Get adequacies
# NOTE: pixi is not yet installed on this cluster - comment out until it is.
for run_name in APS_base_allflex ; do
  for operun in R2030 R2040 R2050; do
    if [[ ! " ${not_allowed_runs[*]} " =~ " ${run_name}_${operun} " ]]; then
      pixi run analyse adequacy "${run_name}_${operun}"
    fi
  done
done
