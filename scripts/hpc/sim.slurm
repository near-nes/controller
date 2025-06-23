#!/bin/bash

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=7
#SBATCH --mem=30GB
#SBATCH --time=00:10:00
#SBATCH --out=slurm.%j.out
#SBATCH --err=slurm.%j.err
#SBATCH --account=<Account_name>
#SBATCH --partition=g100_usr_prod
export OMP_NUM_THREADS=7

module purge
module load openmpi/4.1.6--gcc--12.2.0

mpirun -np 7 singularity exec \
    --bind ./scratch:/scratch_local \
    --bind ./results:/sim/controller/runs \
    --bind ./artifacts:/sim/controller/artifacts \
    --bind ./tmp:/tmp \
    sim.sif/ music /sim/controller/complete_control/complete.music

# --bind ./scratch:/scratch_local \ openMPI coordinates using files in here
# --bind ./results:/sim/controller/runs \ 
# --bind ./artifacts:/sim/controller/artifacts \ for base hdf5 network uncompressing
# --bind ./tmp:/tmp \ openMPI coordinates using files in here (i think)