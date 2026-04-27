ARG PYTHON_MAJOR=3
ARG PYTHON_MINOR=10

FROM ubuntu:jammy AS base

ARG PYTHON_MAJOR
ARG PYTHON_MINOR

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    ffmpeg \
    # nest-simulator dependencies, partly from https://nest-simulator.readthedocs.io/en/stable/installation/noenv_install.html#noenv
    gsl-bin \
    libgsl27 \
    libltdl7 \
    # libboost-dev \
    libgomp1 \
    libreadline8 \
    libhdf5-dev \
    python3-venv \
    python-is-python3 \
    gosu \
    vim \
    gzip \
    tar \
    wget \
    # --- VNC Dependencies ---
    tigervnc-standalone-server \
    tigervnc-common \
    tigervnc-tools \
    fluxbox \
    xterm

# nrp-core dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gnupg2 \
    software-properties-common \
    sudo
RUN add-apt-repository ppa:pistache+team/unstable
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libboost-filesystem1.74.0 \
    libboost-python1.74.0 \
    libboost-numpy1.74.0 \
    libbrotli1 \
    libcurl4 \
    libgrpc++1 \
    libpistache0 \
    libprotobuf23 \
    libzip-dev \
    nlohmann-json3-dev

ENV BUILD_UID=1000
ENV BUILD_GID=1000
ENV USERNAME=simuser
RUN set -eux; \
    if ! getent group ${BUILD_GID} >/dev/null; then \
    groupadd --gid ${BUILD_GID} "$USERNAME"; \
    fi; \
    useradd --uid ${BUILD_UID} --gid ${BUILD_GID} --create-home --shell /bin/bash "$USERNAME"; \
    echo "${USERNAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN mkdir /sim && chown $USERNAME:$USERNAME /sim

USER $USERNAME
ARG PYTHON_MAJOR
ARG PYTHON_MINOR


WORKDIR /sim
ENV VIRTUAL_ENV=/sim/venv
RUN python -m venv --system-site-packages $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY ./docker/constraints.txt /tmp/constraints.txt
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/
ENV UV_PYTHON="$VIRTUAL_ENV/bin/python"
# pip is installed: nrp-core's CMake build uses it
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --upgrade pip setuptools wheel packaging flit_core -c /tmp/constraints.txt

ENV INSTALL_DIR=/sim/install
ENV DEPS_DIR=/sim/dependencies
ENV NEST_INSTALL_DIR=$INSTALL_DIR/nest
ENV OMPI_INSTALL_DIR=$INSTALL_DIR/openmpi

ENV CONTROLLER_DIR=/sim/controller
ENV SHARED_DATA_DIR=/sim/shared_data
ENV NEST_MODULE_PATH=/sim/install/nest/lib/nest
ENV NEST_PYTHON_MODULE_PATH=${NEST_INSTALL_DIR}/lib/python${PYTHON_MAJOR}.${PYTHON_MINOR}/site-packages/nest
RUN mkdir -p $CONTROLLER_DIR $SHARED_DATA_DIR $NEST_MODULE_PATH

ENV CEREBELLUM_PATH=/sim/cerebellum

RUN mkdir -p $INSTALL_DIR $DEPS_DIR $NEST_INSTALL_DIR

# openmpi and nest
FROM base AS builder

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libtool \
    cmake \
    libgsl-dev \
    libltdl-dev \
    libreadline-dev \
    python3-dev

# nrp-core dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    doxygen \
    libboost-filesystem-dev \
    libboost-numpy-dev \
    libboost-python-dev \
    libbrotli-dev \
    libclang-dev \
    libcurl4-openssl-dev \
    libgrpc++-dev \
    llvm-dev \
    llvm \
    libprotobuf-dev \
    protobuf-compiler-grpc \
    libpistache-dev

ENV PATH="${VIRTUAL_ENV}/bin:${NEST_INSTALL_DIR}/bin:${OMPI_INSTALL_DIR}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${OMPI_INSTALL_DIR}/lib:${LD_LIBRARY_PATH}"
ENV PKG_CONFIG_PATH="${OMPI_INSTALL_DIR}/lib/pkgconfig"

####################### openMPI #####################
WORKDIR ${DEPS_DIR}
ENV OMPI_DIR=${DEPS_DIR}/openmpi-4.1.6
ENV OMPI_GZ=openmpi-4.1.6.tar.gz
RUN wget --output-document $OMPI_GZ https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-4.1.6.tar.gz
RUN tar xfz $OMPI_GZ \
    && cd $OMPI_DIR \
    # --enable-mpi-cxx enables old c++ bindings for nest 3.7
    && ./configure --prefix=$OMPI_INSTALL_DIR --enable-mpi-cxx\
    && make -j$(nproc) \
    && make install

ENV CFLAGS=-O2
# ^ for https://github.com/mpi4py/mpi4py/issues/652

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install cython mpilock mpi4py -c /tmp/constraints.txt
ENV CFLAGS=

WORKDIR $DEPS_DIR

####################### NEST 3.9 #######################
ENV NEST_VERSION=3.9

# Install NEST 3.9
WORKDIR $DEPS_DIR
RUN git clone --depth 1 --branch v${NEST_VERSION} https://github.com/nest/nest-simulator/
WORKDIR ${DEPS_DIR}/nest-simulator

RUN mkdir -p nest-build \
    && cd nest-build \
    && cmake -DCMAKE_INSTALL_PREFIX:PATH=$NEST_INSTALL_DIR \
    -Dwith-mpi=ON \
    -Dwith-python=ON \
    # just to make extra extra sure
    -DPYTHON_EXECUTABLE=$VIRTUAL_ENV/bin/python \
    -Dwith-openmp=ON \
    -Dwith-ltdl=ON \
    # -Dstatic-libraries=ON \ i tried this, but it didn't work. i don't think it's maintained
    # -DCMAKE_C_COMPILER=mpicc -DCMAKE_CXX_COMPILER=mpicxx \
    $DEPS_DIR/nest-simulator \
    && make -j$(nproc) \
    && make install


####################### NRP #######################
ENV NRP_INSTALL_DIR=${INSTALL_DIR}/nrp
ENV NRP_DEPS_INSTALL_DIR=${INSTALL_DIR}/nrp_deps

# nrp-core tests dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    cppcheck \
    libgmock-dev \
    xvfb
# unclear nrp-core dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    pkg-config


COPY ./docker/requirements_nrp.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements_nrp.txt -c /tmp/constraints.txt --no-build-isolation

ENV NRP_SRC_DIR=/tmp/nrp-core-src
ENV CMAKE_CACHE_FILE=${NRP_SRC_DIR}/.ci/cmake_cache/t3_4.cmake
ARG NRP_CORE_SHA=25a73b5a711bec034cac353f7f583f840e51f817
RUN git clone https://bitbucket.org/hbpneurorobotics/nrp-core.git ${NRP_SRC_DIR} \
    && cd ${NRP_SRC_DIR} \
    && git fetch origin ${NRP_CORE_SHA} \
    && git checkout ${NRP_CORE_SHA}
COPY --chown=${USERNAME} docker/nrp_t3_4.cmake ${CMAKE_CACHE_FILE}
RUN cd ${NRP_SRC_DIR} && bash .ci/11-prepare-build.sh && bash .ci/20-build.sh


####################### CEREBELLUM+MODELS #######################
RUN git clone https://github.com/near-nes/cerebellar-models $CEREBELLUM_PATH \
    && cd $CEREBELLUM_PATH \
    && git checkout 4403f7e6c91063e6737cc410410d342df9598fa9 \
    && pip install --no-deps . \
    && cd custom_stdp \
    && cmake . \
    && make \
    && make install
# allow all users to run git commands here
RUN git config --global --add safe.directory $CEREBELLUM_PATH 

FROM builder AS package_install
WORKDIR /tmp/pkg
# Copy only files needed for dependency resolution.
COPY pyproject.toml README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r pyproject.toml -c /tmp/constraints.txt --no-build-isolation \
    --extra-index-url https://download.pytorch.org/whl/cpu

# final runtime image
FROM base AS runtime

ENV NRP_INSTALL_DIR=${INSTALL_DIR}/nrp
ENV NRP_DEPS_INSTALL_DIR=${INSTALL_DIR}/nrp_deps

ENV PATH="${VIRTUAL_ENV}/bin:${NRP_INSTALL_DIR}/bin:${NEST_INSTALL_DIR}/bin:${OMPI_INSTALL_DIR}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${OMPI_INSTALL_DIR}/lib:${NRP_INSTALL_DIR}/lib:${NRP_DEPS_INSTALL_DIR}/lib:${LD_LIBRARY_PATH}"

COPY --from=builder ${INSTALL_DIR} ${INSTALL_DIR}
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder ${CEREBELLUM_PATH} ${CEREBELLUM_PATH}
COPY --from=package_install ${VIRTUAL_ENV} ${VIRTUAL_ENV}
# install dirs world-readable (venv writable so users can pip install)
USER 0
RUN chmod -R a+rX ${INSTALL_DIR} ${CEREBELLUM_PATH} \
    && chmod -R a+rwX ${VIRTUAL_ENV}
USER $USERNAME
ENV MPLCONFIGDIR=/tmp/matplotlib
# openMPI needs this if no ssh/rsh available
ENV OMPI_MCA_plm=^rsh

# suppress nest startup message
ENV PYNEST_QUIET=1

# RUNS_PATH is left unset so it defaults to $CWD/runs (where run-trials is invoked).
# EMBODIMENT_ASSETS_PATH can be set to override the bundled package assets.

ENV PYTHON_MAJOR_MINOR="python${PYTHON_MAJOR}.${PYTHON_MINOR}"

# point nest to nest installation
RUN echo ${NEST_INSTALL_DIR}/lib/${PYTHON_MAJOR_MINOR}/site-packages >> ${VIRTUAL_ENV}/lib/${PYTHON_MAJOR_MINOR}/site-packages/nest.pth
# pythonpath construction (note: CONTROLLER_DIR no longer needed as package is installed via pip)
ENV PYTHONPATH="${NRP_INSTALL_DIR}/lib/python${PYTHON_MAJOR}.${PYTHON_MINOR}/site-packages${PYTHONPATH:+:${PYTHONPATH}}"
RUN echo "Constructed PYTHONPATH: ${PYTHONPATH}"

WORKDIR /sim

# Expose VNC port (Display :1 is 5901)
EXPOSE 5901
ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]

USER 0
COPY ./docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
# >>>>>>>>>> VNC SETUP >>>>>>>>>>>>>>
ENV VNC_DISPLAY=":1"
ENV DISPLAY="${VNC_DISPLAY}"
COPY scripts/services/start-vnc.sh /usr/local/bin/start-vnc.sh
RUN chmod +x /usr/local/bin/start-vnc.sh

RUN mkdir -p /home/simuser/.vnc
COPY scripts/services/xstartup /home/simuser/.vnc/xstartup
RUN chmod 700 /home/$USERNAME/.vnc/xstartup
RUN chown -R simuser:simuser /home/$USERNAME/.vnc
RUN chmod 777 -R  /home/$USERNAME/.vnc

# ensure env is loaded for all shells
# login shells
COPY scripts/env/* /etc/profile.d/
RUN chmod +x /etc/profile.d/*

# non-login interactive bash shells
RUN mkdir -p /etc/bashrc.d
COPY scripts/env/* /etc/bashrc.d/
RUN chmod +x /etc/bashrc.d/*
# interactive bash shells
RUN echo 'if [ -d /etc/bashrc.d ]; then for f in /etc/bashrc.d/*; do [ -f "$f" ] && . "$f"; done; fi' \
    >> /etc/bash.bashrc
# (everything else is unsupported)
RUN echo "export DISPLAY=${VNC_DISPLAY}" >> /etc/bash.bashrc

# FROM nrp-runtime AS dev
FROM runtime AS dev
# In dev, the controller directory is mounted from the host and the user is the same as the host user.
ENV SIMULATION_MODE=dev

# dev deps
COPY pyproject.toml /tmp/pyproject.toml
RUN --mount=type=cache,target=/home/simuser/.cache/uv \
    cd /tmp && uv pip install --group dev -c /tmp/constraints.txt

FROM runtime AS prod
ENV UV_COMPILE_BYTECODE=1
ENV SIMULATION_MODE=prod

# In prod, dependencies are already installed (via package_install stage).
# The package itself and sibling packages are installed here from the copied source.
COPY --chown=${USERNAME} submodules ${CONTROLLER_DIR}/submodules
COPY --chown=${USERNAME} . ${CONTROLLER_DIR}
WORKDIR ${CONTROLLER_DIR}
RUN --mount=type=cache,target=/home/simuser/.cache/uv \
    uv pip install . --no-deps --no-build-isolation
RUN --mount=type=cache,target=/home/simuser/.cache/uv \
    uv pip install --no-deps --no-build-isolation \
    ./src/neurocontroller/shared/minjerk \
    ./submodules/motor_cortex_eprop \
    ./submodules/pfc_planner

# HPC compatibility target (same image content as prod, different mode flag)
FROM prod AS hpc
ENV UV_COMPILE_BYTECODE=1
ENV SIMULATION_MODE=hpc