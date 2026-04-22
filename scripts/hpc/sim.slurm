#!/bin/bash
#SBATCH --job-name=neurocontroller
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=g100_usr_prod
#SBATCH --account=<Account_name>

# Launch the neurocontroller simulation inside the Singularity image on CINECA G100.
#
# Prerequisites on the login node:
#   - $HOME/sim.sif built from scripts/hpc/sim.def (see scripts/utilities/build_and_export.sh)
#   - $HOME/scratch and $HOME/runs writable (script creates them)
#
# Override paths via env vars: SIF, RUNS_DIR, SCRATCH_DIR.
# Submit with:  sbatch scripts/hpc/sim.slurm
# For short debug jobs, switch --partition to g100_all_serial.

set -euo pipefail

SIF=${SIF:-$HOME/sim.sif}
RUNS_DIR=${RUNS_DIR:-$HOME/runs}
SCRATCH_DIR=${SCRATCH_DIR:-$HOME/scratch}

mkdir -p "$SCRATCH_DIR" "$RUNS_DIR"

module load singularity 2>/dev/null || true

echo "Node:    $(hostname)"
echo "Date:    $(date)"
echo "SIF:     $SIF"
echo "RUNS:    $RUNS_DIR"
echo "SCRATCH: $SCRATCH_DIR"

# RUNS_PATH is exported into the container so both the client process (CWD=$HOME)
# and the NRP engine subprocesses (CWD=/sim/controller) land in the same run directory
# instead of splitting across $HOME/runs and the bound /sim/controller/runs.
singularity exec \
    --bind "$SCRATCH_DIR:/scratch_local" \
    --env RUNS_PATH="$RUNS_DIR" \
    "$SIF" \
    python -m neurocontroller.nrp_start_sim
