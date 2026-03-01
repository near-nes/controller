# Controller setup instructions

This project is currently based on six main libraries
- [NEST simulator](https://github.com/nest/nest-simulator/releases/tag/v3.7): this is our neural simulator
- cerebellum model: details population and connectivity patterns in the cerebellum
- [BSB framework](https://bsb.readthedocs.io/en/latest/index.html): builds cerebellar network based on the model recipe
- [pyBullet simulator](https://github.com/bulletphysics/bullet3): the physics simulator which simulates the robotic plant
- [cerebellar models](https://github.com/dbbs-lab/cerebellar-models/tree/feature/plasticity): the `bsb` configuration tree that contains a plastic model of the cerebellum
- [NRP-core](https://bitbucket.org/hbpneurorobotics/nrp-core/src/master/): the coordinator and data manager between the two simulations

and uses, in addition to our own code, a few supporting repos:
- pyBullet [muscle simulation](https://github.com/UM-Projects-MZ/bullet_muscle_sim)
- [skeletal model](https://github.com/UM-Projects-MZ/embodiment_sdf_models)
- [motor cortex](https://github.com/INM-6/motor-controller-model) (soon to be released)
- [prefrontalcortex planner](https://github.com/paulhaider/pfc-planner)

All of this needs to be MPI-compatible, so the setup is somewhat involved. In this document, we'll first get you going and then document some additional information for future-proofing.

## Basic setup
For this, you'll need [docker](https://docs.docker.com/engine/install/) already set up and working. We'll assume you've done the setup to use it without `sudo`, but you must understand that Docker (and our image) still has [real power](https://docs.docker.com/engine/security/#docker-daemon-attack-surface) over your system. The `controller/` directory will be mounted as a bind mount, and the container image _will_ create files inside it on your behalf.

0. Clone this repository at the correct branch and enter the directory 
```sh
git clone <controller_repo_url> controller && cd controller && git checkout complete_control_cereb
```
1. Create variables for your user id and group id and save them to an env file (so that you don't need to do this again).
```sh
echo -e "UID=$(id -u)\nGID=$(id -g)" > .env
```
2. Build and run the container:
```sh
docker compose run --build --rm development
```
3. Now, you're ready to use the image as a devcontainer. Just open the folder in `vscode` and click on "reopen in container". You can pick a command to run from the `docker-compose.yml`

> [!NOTE]
> The first run will take longer. Optimize startup time by building the image with the user who will be the runner; the bind mounted `controller/` directory is owned by you.

## Further information
There's a few important pieces of information you should have if you're looking to update, modify or understand the `docker-compose.yaml` or the corresponding dockerfile. Of course, these are tightly related to the process.

### A super simple overview of what happens
The network connectivity, morphology and populations are defined in `/sim/cerebellum/`, to be used by `BSB`. It includes custom models in `custom_stdp`, and the configuration file for `BSB` (together with nest parameters) in `/sim/cerebellum/configurations/dcn-io/microzones_complete_nest.yaml`. In order to understand the build, you should read the [intro to BSB](https://bsb.readthedocs.io/en/latest/getting-started/top-level-guide.html#get-started).
- The custom models in `/sim/cerebellum/custom_stdp` are compiled and placed in a directory NEST can find them in
- The base cerebellum model is compiled using `bsb compile ...` to an hdf5 file. We include a pre-compiled version in `/artifacts/`
- The simulation is started _by_ the coordinator, either MUSIC or NRP which coordinate the communication between NEST simulation and the robotic plant

### Python
Most of the libraries provide bindings for (or are entirely built in) Python. This makes it fundamental that the python environment is stable and accessible. We achieve this by always starting from the same image, and using a single virtual environment.

#### Package versions
Needed packages are installed throughout the Dockerfile, limited by `docker/constraints.txt`. The distribution of installed packages (as opposed to a single requirements.txt file) has multiple reasons: some need to use specific indexes (CPU-only versions of pytorch); `mpi4py` requires compilation and its version is unlikely to change, so it is installed in an early layer of the image; some packages are needed to install `NEST`, while others can be installed later to parallelize downloads, and so on.

If you need to add an additional package, [`requirements`](docker/requirements.txt) is where you should do so. Include the package version in [`constraints`](docker/constraints.txt).

### Users and permissions
The current setup maximizes flexibility, at the cost of stability and speed: because the "working directory" (both repositories) are mounted as volumes, and some scripts need to write into them, the container needs a non-root user with the same user id and group id as the user running the container. Since these ids are not known at build time, the container creates a non-root user which will then be "converted" to the one running the user: the `entrypoint.sh` script verifies if the user/group id has changed and `chown`s the venv and home directories. This is why giving the correct ids at build time enables faster run startup: if the non-root directories were already `chown`ed correctly during the build, you'll never suffer the performance hit at run.

We understand this is not the perfect setup; once again, it is optimized for flexibility during development; a production image could just install all repositories and only write results in a mounted folder.

### Custom NEST modules
Cerebellum uses custom NEST models. NEST modules are cpp files that need to be compiled and linked against NEST before use. We do this in the image build. These models were generated using NESTML, from the module in `complete_control/deprecated/controller_module.nestml`; because they are very stable, we directly use the *.cpp files included in the `cerebellar_models` and don't include NESTML in this image.
You might be thinking: but can't we just use a non-standard location for custom modules instead? Although NEST specifically [advises against this](https://nest-extension-module.readthedocs.io/en/latest/extension_modules.html#building-mymodule), it would be possible as far as NEST custom models go. Instead, it seems that NESTML does [not](https://github.com/nest/nestml/issues/480) have this option (I attempted using it, but it did not work).

### Additional info
- NEST static build: doesn't work.
- multi-stage build: tried it... caused mis-aligned scipy/numpy versions, not sure why