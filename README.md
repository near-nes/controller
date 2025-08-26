# Controller

This project involves multiple codebases interacting. In an attempt to make the results more reproducible, and to enable HPC simulations, we're creating a containerized setup. You can find more information in [INSTALL.md](INSTALL.md).

This branch of the repository features all code needed to run simulations of reaching tasks on a virtual robotic arm driven by a closed-loop cerebellar controller.

The file `complete_control/complete.music` defines the two Python scripts containing the two simulations to be synchronized by MUSIC. The NEST simulation is run by `complete_control/main_simulation.py` and the PyBullet simulation by `complete_control/receiver_plant.py`. The file `./complete_control/complete.music` can be modified to allocate the desired number of slots (i.e. MPI procs) to both the controller script and the plant one. The simulation can be started by running:
`mpirun -np <tot_number_procs> music complete.music` from `./complete_control`. The value of the -np parameter should be adjusted according to the number of processes allocated in the `complete.music` file.

The folder `config` contains several pydantic models used for parameters. A specific configuration can be exported to and from JSON.

We develop this using a devcontainer, made to the specifications of `devcontainer.json`, `docker-compose` and `docker/Dockerfile`. The HPC version is also generated from the container.

## HPC
Quick notes before a more complete documentation:
- build the container using `/scripts/build_and_export.sh`
- move the zipped image to HPC
- decompress it
- create necessary folders for mounts (consider that the singularity container is fully read-only) `mkdir scratch results artifacts tmp`
- create the singularity container: `singularity build sim.sif docker-archive://sim.tar`

### MUSIC and MPI
- load openmpi module
- allocate what you need: `salloc --ntasks-per-node=7 --mem=23000MB --account=<your_account_name> --time=01:00:00 --partition=g100_usr_interactive`
- run the simulation: `mpirun -np 7 singularity exec --bind ./scratch:/scratch_local --bind ./results:/sim/controller/runs --bind ./artifacts:/sim/controller/artifacts --bind ./tmp:/tmp sim.sif/ music /sim/controller/complete_control/complete.music`

### NRP without MPI
- edit `scripts/hpc/batch_job.sh` to make sure you have a valid resource allocation and run command
- copy it to the HPC
- run it with `sbatch batch_job.sh`


Optionally, mount (`--bind`) `complete_control` for "live" code changes. If paired with vscode remote, you can almost have a fully interactive development session on the cluster... Not sure if there's a way to do client vscode -> cineca HPC -> devcontainer, might check [this](https://github.com/microsoft/vscode-remote-release/issues/3066#issuecomment-1019500216)


## Build NRP image

checkout recursively git submodules

```
docker compose build

docker compose -f nrp_docker-compose-nest-pybullet.yaml up

```
