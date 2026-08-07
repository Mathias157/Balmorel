#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=rome
### -- set the job Name --
#SBATCH --job-name=analysis
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=2
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=0-01:00:00
### -- send notification at completion --
#SBATCH --mail-type=END
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=logs/analysis_%j.out
#SBATCH --error=logs/analysis_%j.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source jobs/slurm/functions.sh

# Load user functions (generate_plots)
source jobs/userfunctions.sh

# Get scenario choice and run name from jobs/scenario_choice.sh
source jobs/scenario_choice.sh

for scenario in APS_base_allflex; do
    for runtype in R2030 R2040 R2050; do
        # This will fail if the scenario name is incorrect, e.g. if it's named after the scenario folder instead of MainResults suffix!
        year=$(echo $runtype | tail -c 5)
        echo "Plotting year ${year} for run ${scenario}_${runtype}.."
        generate_plots "${scenario}_${runtype}" $year

        # Remove old collected pdf to ensure no corruption errors in next colleciton
        collected_pdf=analysis/plots/collected_plots_${scenario}_${runtype}.pdf
        if [[ -f "$collected_pdf" ]]; then
            rm analysis/plots/collected_plots_${scenario}_${runtype}.pdf
        fi
        pdfunite analysis/plots/*${scenario}_${runtype}.pdf $collected_pdf
    done
done
