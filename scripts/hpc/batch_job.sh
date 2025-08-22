#!/bin/bash
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --partition=g100_all_serial

singularity exec \
    --bind ./scratch:/scratch_local \
    --bind ./results:/sim/controller/runs \
    --bind ./tmp:/tmp  \
    --env PYNEST_QUIET=0 \
    --env EXEC_TIMESTAMP=$(date +%Y%m%d_%H%M%S) \
    sim.sif/ /usr/local/bin/entrypoint.sh NRPCoreSim -c /sim/controller/nrp_simulation_config_nest_singularity.json --cloglevel debug --floglevel debug --logdir /tmp/logs
