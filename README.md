# Controller

This project involves multiple codebases interacting. In an attempt to make the results more reproducible, and to enable HPC simulations, we're creating a containerized setup. You can find more information in [INSTALL.md](INSTALL.md).

This branch of the repository features the core code needed to run simulations of reaching tasks on a virtual robotic arm driven by a closed-loop cerebellar controller. Various sub-modules are implemented in different repos: you'll need to clone all gitmodules (`git submodule update --init --recursive`) to run all possible configurations.

As the project involves multiple simulators, the interaction between them is governed by a *coordinator*. We used to support two possible coordinators: **MUSIC** and **NRP**, but we've now deprecated MUSIC and only focus on NRP.


## NRP

NRP is a simulation coordinator, which expects simulation specifications (called "engines") to implement specific interfaces. Its configuration is replicated in a pydantic model in `complete_control/config/nrp_sim_config.py`, where you can find pointers to the two simulations: `nrp_neural_engine.py` and `nrp_bullet_engine.py`. As the loop component is inside the NRP, these files offer only single step functions. 

## Simulations

The folder `config` contains several pydantic models used for parameters. The main object is `MasterParams.py`; beyond this, you may need to edit `core_models.py` to change trajectories and simulation specifications, and `module_params.py` to specify which submodule to use for planner and M1 sections. A specific configuration can be exported to and from JSON.

## Development
We develop this using a (docker) devcontainer, made to the specifications of `devcontainer.json`, `docker-compose` and `docker/Dockerfile`. The HPC container (singularity) is also created from the docker container.

### Using the Pip-Installable Package in Development

The experiment can be installed as a Python package (`near-nes-controller`) for both development and production use.

#### Quick Setup (dev container)

In dev mode, the package is automatically installed in editable mode when the container starts:

```bash
# Just run the container - package installation happens automatically
docker compose run development

# Inside the container, you can now use:
run-trials 10 --label "my_experiment"
```

Changes you make to source files in `complete_control/` are immediately reflected—no reinstall needed.

#### Quick Setup (local venv)

If you already have a virtual environment with dependencies installed locally:

```bash
# Install the package in editable (development) mode
pip install -e .

# Now you can run the experiment
run-trials 10 --label "my_experiment"
```

In editable mode (`-e`), changes you make to source files in `complete_control/` are immediately reflected when you run the package—no reinstall needed.

#### Package features
- **Entry point**: `run-trials` command wraps `complete_control/run_trials.py`
- **Data files**: Automatically locates `artifacts/` and `cerebellum_configurations/` from the installed package
- **BSB decompression**: Automatically decompresses `cerebellum_plastic_base.hdf5.gz` on first import
- **Backward compatible**: Still respects `CONTROLLER_DIR` environment variable if set (for Docker/HPC mounts)

#### Building the package

To create distributable wheels and source distributions:

```bash
python -m pip install build
python -m build

# Outputs to dist/
# - near_nes_controller-0.1.0.tar.gz (source distribution)
# - near_nes_controller-0.1.0-py3-none-any.whl (wheel, if built)
```

## Build and run the container
`echo -e "UID=$(id -u)\nGID=$(id -g)" > .env && docker compose build`
You only need to create the `.env` once. This file is used to synchronize directories internally for live code editing. 
Then, you can either open a devcontainer using it or `docker compose run development`. For more info, see `INSTALL.md`

## HPC
Quick notes before a more complete documentation:
- build the container using `scripts/utilities/build_and_export.sh`, optionally specifying a remote to copy the built container to (as `<username>@<host>`, SSH should be possible to this endpoint).
- if you don't specify the remote, manually:
    - move the zipped image to HPC
    - decompress it
    - create the singularity container: `singularity build sim.sif docker-archive://sim.tar`
- create necessary folders **in HPC** for mounts (consider that the singularity container is fully read-only) `mkdir scratch results tmp`, then keep reading depending on what coordinator you're using.


### NRP without MPI
- edit `scripts/hpc/batch_job.sh` to make sure you have a valid resource allocation and run command
- copy it to the HPC
- run it with `sbatch batch_job.sh`


Optionally, mount (`--bind`) `complete_control` for "live" code changes. If paired with vscode remote, you can almost have a fully interactive development session on the cluster... Not sure if there's a way to do client vscode -> cineca HPC -> devcontainer, might check [this](https://github.com/microsoft/vscode-remote-release/issues/3066#issuecomment-1019500216)


## MUSIC - Deprecated

Although basic usage still likely works, using MUSIC is deprecated. Please use NRP instead.

MUSIC is an API that allows data exchange between simulators, implemented with MPI primitives. As it only focuses on data exchange (and between-process coordination), the main simulation loop is explicit and out of MUSIC control. Every MUSIC run is an MPI run (in fact, you run music directly with `mpirun`). NEST provides strong integration with MUSIC, so there are few explicit MUSIC calls in our neural-side implementation, which instead uses "MUSIC proxies", neuron models with MUSIC calls inside them. The robotic side, instead, needs explicit MUSIC calls.

The main MUSIC configuration file is `complete_control/complete.music`. It defines the two Python scripts containing the two simulations to be synchronized by MUSIC. The NEST simulation is run by `complete_control/music_start_sim.py` and the PyBullet simulation by `complete_control/receiver_plant.py`. The file `./complete_control/complete.music` can be modified to allocate the desired number of slots (i.e. MPI procs) to both the controller script and the plant one. The simulation can be started by running: `mpirun -np <tot_number_procs> music /sim/controller/complete_control/complete.music` from `./complete_control`. The value of the -np parameter must correspond to the configuration file

### MUSIC and MPI - Deprecated
- load openmpi module, export PMIX_MCA_gds=hash to [suppress PMIX warning](https://docs.hpc.cineca.it/services/singularity.html#parallel-mpi-container)
- allocate what you need: `salloc --ntasks-per-node=7 --mem=23000MB --account=<your_account_name> --time=01:00:00 --partition=g100_usr_interactive`
- run the simulation: `mpirun -np 7 singularity exec --bind ./scratch:/scratch_local --bind ./results:/sim/controller/runs --bind ./artifacts:/sim/controller/artifacts --bind ./tmp:/tmp sim.sif/ music /sim/controller/complete_control/complete.music`