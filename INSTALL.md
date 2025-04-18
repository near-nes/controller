# Controller setup instructions

This project is currently based on five main libraries
- [NEST simulator](https://github.com/nest/nest-simulator/releases/tag/v3.7): this is our neural simulator
- [MUSIC interface](https://github.com/INCF/MUSIC): enables communication between NEST and the physics simulation
- cerebellum model: details population and connectivity patterns in the cerebellum
- [BSB framework](https://bsb.readthedocs.io/en/latest/index.html): builds cerebellar network based on the model recipe
- [pyBullet simulator](https://github.com/bulletphysics/bullet3): the physics simulator which simulates the robotic plant

and uses, in addition to our own code, a few supporting repos:
- pyBullet [muscle simulation](https://github.com/UM-Projects-MZ/bullet_muscle_sim)
- [skeletal model](https://github.com/UM-Projects-MZ/embodiment_sdf_models)

All of this needs to be MPI-compatible, so the setup is somewhat involved. In this document, we'll first get you going and then document some additional information for future-proofing.

## Basic setup
For this, you'll need [docker](https://docs.docker.com/engine/install/) already set up and working. We'll assume you've done the setup to use it without `sudo`, but you must understand that Docker (and our image) still has [real power](https://docs.docker.com/engine/security/#docker-daemon-attack-surface) over your system. The `controller/` directory will be mounted as a bind mount, and the container image _will_ create files inside it on your behalf.

0. Clone this repository at the correct branch and enter the directory 
```sh
git clone <controller_repo_url> controller && cd controller && git checkout complete_control_cereb
```
1. Clone the cerebellum repo at the correct branch INTO the controller directory
```sh
git clone <cerebellum_repo_url> cerebellum cerebellum && cd cerebellum && git checkout feature/plasticity && cd ..
```
2. Create variables for your user id and group id and save them to an env file (so that you don't need to do this again).
```sh
echo -e "UID=$(id -u)\nGID=$(id -g)\nVNC_PASSWORD=somepassword" > .env
```
2. Build the container image
```sh
docker compose build
```
3. Run it
```sh
docker compose run simulation
```
4. All in one:
```sh
docker compose run --build --rm simulation
```

> [!NOTE]
> The first run will take longer. Optimize startup time by building the image with the user who will be the runner; the bind mounted `controller/` directory is owned by you.

## Further information
There's a few important pieces of information you should have if you're looking to update, modify or understand the `docker-compose.yaml` or the corresponding dockerfile. Of course, these are tightly related to the process.

### A super simple overview of what happens
The network connectivity, morphology and populations are defined in `cerebellum/`, to be used by `BSB`. It includes custom models in `custom_stdp`, and the configuration file for `BSB` (together with nest parameters) in [`cerebellum/configurations/dcn-io/microzones_complete_nest.yaml`](cerebellum/configurations/dcn-io/microzones_complete_nest.yaml). In order to understand the build, you should read the [intro to BSB](https://bsb.readthedocs.io/en/latest/getting-started/top-level-guide.html#get-started).
- The custom models in [`cerebellum/custom_stdp`](cerebellum/custom_stdp) are compiled and placed in a directory NEST can find them in
- The model is compiled using `bsb compile ...` to an hdf5 file
- The trajectory and motor commands are generated by a [dedicated script](complete_control/generate_analog_signals.py)
- The simulation is started _by_ MUSIC (`music complete_control/brain.py`), which coordinates the communication between NEST simulation and the robotic plant. One important detail is that the simulation is controlled by `brain.py`, **not** by `BSB`, so `BSB` must be available when running the simulation as well.

### Python
Most of the libraries provide bindings for (or are entirely built in) Python. This makes it fundamental that the python environment is stable and accessible. We achieve this by always starting from the same python image (right now `python:3.10-slim-bookworm`), and using a single virtual environment, which lives in a volume. The volume _may_ be removed in the future, but currently all repos are private (and we don't want to rely on ssh keys from the current user), so parts need to be installed at runtime; additionally, `controller/cerebellum/` is installed in editable mode (`pip install -e`) to enable changes to be reflected in the image, so there was no way around it.

#### Package versions
Needed packages are included in [`requirements_base`](requirements_base.txt) and [`requirements`](requirements.txt). Since `mpi4py` requires compilation and its version is unlikely to change, we decided to include it in an early layer of the image. Other requirements are pinned to the needed versions by `cerebellum`.

If you need to add an additional package, this is where you should do so. Include the package version.
Important note: because /sim/venv is mounted as a volume, after the first volume creation (i.e. the first `docker compose run`) it will _never_ be updated with the image contents of `/sim/venv`. To avoid surprising situations, on every run of the container a silent `pip install -r requirements.txt` is run: if the environment is already as expected, this is a no-op; otherwise, missing packages are installed. If you edit `requirements.txt`, every time the container starts it will download and install any packages which are (a) present in the base image, but (b) not present in the volume. To make sure that the contents of `/sim/venv` are consistent with what is present in the base image, after stopping the container run `docker compose down -v`: this will delete all volumes, so that on the next start they can be initialized to the current contents of `/sim/venv` as specified _by the image_. This will reduce your start-up time, as pip won't need to install packages on every container run.

### Users and permissions
The current setup maximizes flexibility, at the cost of stability and speed: because the "working directory" (both repositories) are mounted as volumes, and some scripts need to write into them, the container needs a non-root user with the same user id and group id as the user running the container. Since these ids are not known at build time, the container creates a non-root user which will then be "converted" to the one running the user: the `entrypoint.sh` script verifies if the user/group id has changed and `chown`s the venv and home directories. This is why giving the correct ids at build time enables faster run startup: if the non-root directories were already `chown`ed correctly during the build, you'll never suffer the performance hit at run.

We understand this is not the perfect setup; once again, it is optimized for flexibility. Once these repositories are stable, they can be copied into the base image and there won't be any installing at container run.

### Custom NEST modules
Cerebellum uses both custom NEST modules and custom NESTML models. NEST modules are cpp files that need to be compiled and linked against NEST before use. NESTML are written in a custom syntax and compiled (by NESTML) in `~/.cache/nest_build`. They must then be placed somewhere NEST can find them: the default directory is `$NEST_INSTALL/lib/nest`. This means 2 things:
1. `$NEST_INSTALL/lib/nest` should be cached to avoid recompiling custom modules. This led us to creating a volume for its persistence
2. `$NEST_INSTALL/lib/nest` must be writable by the running user. This is accomplished in the same way as the other directories explained in the previous section
You might be thinking: but can't we just use a non-standard location for custom modules instead? Although NEST specifically [advises against this](https://nest-extension-module.readthedocs.io/en/latest/extension_modules.html#building-mymodule), it would be possible as far as NEST custom models go. Instead, it seems that NESTML does [not](https://github.com/nest/nestml/issues/480) have this option (I attempted using it, but it did not work).

### Additional info
- NEST static build: doesn't work.
- multi-stage build: tried it... caused mis-aligned scipy/numpy versions not sure why