#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=rome
### -- set the job Name --
#SBATCH --job-name=temporal_aggregation
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=3
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=0-04:00:00
### -- send notification at completion --
#SBATCH --mail-type=END
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=logs/temporal_aggregation_%j.out
#SBATCH --error=logs/temporal_aggregation_%j.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source jobs/slurm/functions.sh

# Get scenario choice and run name from jobs/scenario_choice.sh
source jobs/scenario_choice.sh

# Define temporal aggregation parameters
scenario_to_agg=base
seasons=8
terms=24
method=kmedoids
representation=medoid

# Do aggregation
# NOTE: pixi is not yet installed on this cluster - comment out until it is.
pixi run python -c "from pybalmorel import Balmorel
m=Balmorel(\".\", gams_system_directory=\"/groups/INP/gams/gams46.5_linux_x64_64_sfx\")
m.temporal_aggregation(\"${scenario_to_agg}\",
                      seasons=${seasons},
                      terms=${terms},
                      method=\"${method}\",
                      representation=\"${representation}\",
                      overwrite=False
)
"

# Make model folder
agg_scenario="${scenario_to_agg}_S${seasons}T${terms}"
if [ ! -d "${agg_scenario}/model" ]; then
    mkdir ${agg_scenario}/model
    cp base/model/Balmorel.gms ${agg_scenario}/model/
    cp base/model/cplex.op2 ${agg_scenario}/model/
    # MANUAL CHANGES:
    rm ${agg_scenario}/data/GDATA.inc
    rm ${agg_scenario}/data/DR_DATAINPUT.inc
fi

echo "FINAL MANUAL STUFF TO DO NOW:
- Figure out which EV profile has the data, and change its suffix to 1
"
# sbatch jobs/slurm/investment.sh
