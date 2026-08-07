for scenario in EVN VGN HPN TPN ELN HSNSSN HSN SSN EIN DCN ALLN H2N; do
    cd $scenario
    sbatch ../jobs/slurm/investment.sh
    cd ..
done
