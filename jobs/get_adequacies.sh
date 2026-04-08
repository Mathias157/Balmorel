#!/bin/sh
### General options
### -- specify queue --
#BSUB -q man
### -- set the job Name --
#BSUB -J get_adequacies
### -- ask for number of cores (default: 1) --
#BSUB -n 5
### -- specify that the cores must be on the same host --
#BSUB -R "span[hosts=1]"
### -- specify that we need 4GB of memory per core/slot --
#BSUB -R "rusage[mem=4.5GB]"
### -- specify that we want the job to get killed if it exceeds 5 GB per core/slot --
#BSUB -M 4.5GB
### -- set walltime limit: hh:mm --
#BSUB -W 2:00
### -- set the email address --
# please uncomment the following line and put in your e-mail address,
# if you want to receive e-mail notifications on a non-default address
##BSUB -u  
### -- send notification at start --
##BSUB -B
### -- send notification at completion --
#BSUB -N
### -- Specify the output and error file. %J is the job-id --
### -- -o and -e mean append, -oo and -eo mean overwrite --
#BSUB -o logs/get_adequacies_%J.out
#BSUB -e logs/get_adequacies_%J.err

# Load error handling and GAMS paths
source jobs/functions.sh

# Get scenario choice and run name from jobs/scenario_choice.sh
source jobs/scenario_choice.sh

# Make exceptions (e.g.: failed runs or runs not finished)
allowed_runs=("APS_base_S8T24MMF1_R2050" "APS_base_S8T24MMF1FLH_R2050" "APS_base_S10T42ST_R2040")

# Get adequacies
for run_name in APS_base_S12T42ST APS_base_S10T42ST APS_base_S8T24MMF1FLH; do
  for operun in R2030 R2040 R2050; do
    if [[ ! " ${allowed_runs[*]} " =~ " ${run_name}_${operun} " ]]; then
      pixi run analyse adequacy "${run_name}_${operun}"
    fi
  done
done

