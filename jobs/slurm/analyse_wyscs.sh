#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windfatq
### -- set the job Name --
#SBATCH --job-name=analysis
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=2
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=0-24:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=logs/analysis_%j.out
#SBATCH --error=logs/analysis_%j.err

cd "$SLURM_SUBMIT_DIR"

source ~/.bashrc

export GAMS_SYSTEM_DIR=/groups/INP/gams/gams53.4_linux_x64_64_sfx/
export PATH=$GAMS_SYSTEM_DIR:$PATH
export LD_LIBRARY_PATH=$GAMS_SYSTEM_DIR:${LD_LIBRARY_PATH:-}

conda activate great

# Load error handling and GAMS paths
# source jobs/slurm/functions.sh

# Load user functions (generate_plots)
# source jobs/userfunctions.sh
# Get scenario choice and run name from jobs/scenario_choice.sh
# source jobs/scenario_choice.sh

# snakemake -s rules/postprocess.smk

python scripts/postprocessing/estimate_flexibility_needs.py --overwrite-cache --output-dir build_postprocess_WY \
    --scenarios base_WY1982_F2050 \
    --scenarios base_WY1983_F2050 \
    --scenarios base_WY1984_F2050 \
    --scenarios base_WY1985_F2050 \
    --scenarios base_WY1986_F2050 \
    --scenarios base_WY1987_F2050 \
    --scenarios base_WY1988_F2050 \
    --scenarios base_WY1989_F2050 \
    --scenarios base_WY1990_F2050 \
    --scenarios base_WY1991_F2050 \
    --scenarios base_WY1992_F2050 \
    --scenarios base_WY1993_F2050 \
    --scenarios base_WY1994_F2050 \
    --scenarios base_WY1995_F2050 \
    --scenarios base_WY1996_F2050 \
    --scenarios base_WY1997_F2050 \
    --scenarios base_WY1998_F2050 \
    --scenarios base_WY1999_F2050 \
    --scenarios base_WY2000_F2050 \
    --scenarios base_WY2001_F2050 \
    --scenarios base_WY2002_F2050 \
    --scenarios base_WY2003_F2050 \
    --scenarios base_WY2004_F2050 \
    --scenarios base_WY2005_F2050 \
    --scenarios base_WY2006_F2050 \
    --scenarios base_WY2007_F2050 \
    --scenarios base_WY2008_F2050 \
    --scenarios base_WY2009_F2050 \
    --scenarios base_WY2010_F2050 \
    --scenarios base_WY2011_F2050 \
    --scenarios base_WY2012_F2050 \
    --scenarios base_WY2013_F2050 \
    --scenarios base_WY2014_F2050 \
    --scenarios base_WY2015_F2050 \
    --scenarios base_WY2016_F2050 \
    --scenarios base_WY2017_F2050 \
    --scenarios base_WY2018_F2050 \
    --scenarios base_WY2019_F2050 \
    --scenarios base_WY2020_F2050
