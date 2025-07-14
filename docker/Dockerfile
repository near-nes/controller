ARG PYTHON_MAJOR=3
ARG PYTHON_MINOR=10

# FROM python:${PYTHON_MAJOR}.${PYTHON_MINOR}-slim-bookworm AS base
FROM ubuntu:jammy AS base

ARG PYTHON_MAJOR
ARG PYTHON_MINOR

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    git \
    # nest-simulator dependencies, partly from https://nest-simulator.readthedocs.io/en/stable/installation/noenv_install.html#noenv
    libtool \
    cmake \
    gsl-bin \
    libgsl-dev \
    libltdl-dev \
    libboost-dev \
    libreadline-dev \
    libhdf5-dev \
    python3-dev \
    python-is-python3 \
    gcc \
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
# && apt-get clean \
# && rm -rf /var/lib/apt/lists/*
RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-venv \
    python3-numpy \
    # python3-matplotlib \
    python3-scipy

ARG USER_UID=1000
ARG USER_GID=1000
ENV USERNAME=simuser
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID --create-home --shell /bin/bash $USERNAME
RUN mkdir /sim && chown $USERNAME:$USERNAME /sim

USER $USERNAME
ARG PYTHON_MAJOR
ARG PYTHON_MINOR
ENV USERNAME=simuser


WORKDIR /sim
ENV VIRTUAL_ENV=/sim/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel

ENV INSTALL_DIR=/sim/install
ENV DEPS_DIR=/sim/dependencies
ENV NEST_INSTALL_DIR=$INSTALL_DIR/nest
ENV MUSIC_INSTALL_DIR=$INSTALL_DIR/music
ENV OMPI_INSTALL_DIR=$INSTALL_DIR/openmpi

ENV CONTROLLER_DIR=/sim/controller
ENV SHARED_DATA_DIR=/sim/shared_data
ENV NEST_MODULE_PATH=/sim/install/nest/lib/nest
RUN mkdir -p $CONTROLLER_DIR $SHARED_DATA_DIR $NEST_MODULE_PATH

ENV CEREBELLUM_PATH=/sim/cerebellum
ENV LD_LIBRARY_PATH="${MUSIC_INSTALL_DIR}/lib"

RUN mkdir -p $INSTALL_DIR $DEPS_DIR $NEST_INSTALL_DIR $MUSIC_INSTALL_DIR

# openmpi, music and nest
FROM base AS builder

ENV PATH="${VIRTUAL_ENV}/bin:${MUSIC_INSTALL_DIR}/bin:${NEST_INSTALL_DIR}/bin:${OMPI_INSTALL_DIR}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${OMPI_INSTALL_DIR}/lib64:${LD_LIBRARY_PATH}"
ENV PKG_CONFIG_PATH="${OMPI_INSTALL_DIR}/lib64/pkgconfig"

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
COPY ./docker/requirements_base.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements_base.txt
ENV CFLAGS=

####################### MUSIC #######################
# Install MUSIC - pinned to last commit to ensure compatibility
WORKDIR $DEPS_DIR

RUN git clone https://github.com/INCF/MUSIC \
    && cd MUSIC \
    && git checkout 6d12edf7094e1dbb473dd55f6fcbd0825f30b811 \
    && ./autogen.sh \
    && ./configure --prefix=$MUSIC_INSTALL_DIR --with-python=$VIRTUAL_ENV/bin/python \
    && make -j$(nproc) \
    && make install

####################### NEST 3.7 #######################
ENV NEST_VERSION=3.7

# Install NEST 3.7
WORKDIR $DEPS_DIR
RUN git clone --depth 1 --branch v${NEST_VERSION} https://github.com/nest/nest-simulator/
WORKDIR ${DEPS_DIR}/nest-simulator

# RUN pip install -r requirements_pynest.txt
RUN mkdir -p nest-build \
    && cd nest-build \
    && cmake -DCMAKE_INSTALL_PREFIX:PATH=$NEST_INSTALL_DIR \
    -Dwith-mpi=ON \
    -Dwith-music=$MUSIC_INSTALL_DIR \
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

# final runtime image
FROM base AS runtime

ENV PATH="${VIRTUAL_ENV}/bin:${MUSIC_INSTALL_DIR}/bin:${NEST_INSTALL_DIR}/bin:${OMPI_INSTALL_DIR}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${OMPI_INSTALL_DIR}/lib64:${LD_LIBRARY_PATH}"

COPY --from=builder ${INSTALL_DIR} ${INSTALL_DIR}
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
# openMPI needs this if no ssh/rsh available
ENV OMPI_MCA_plm=^rsh

# suppress nest startup message
ENV PYNEST_QUIET=1

ENV BULLET_MUSCLE_DIR=$DEPS_DIR/bullet_muscle_sim
ENV SDF_MODELS_DIR=/sim/embodiment_sdf_models
RUN mkdir -p $BULLET_MUSCLE_DIR $SDF_MODELS_DIR

# cerebellum
ENV COMPRESSED_BSB_NETWORK_FILE=${CONTROLLER_DIR}/artifacts/cerebellum_plastic_base.hdf5.gz
ENV BSB_NETWORK_FILE=${CONTROLLER_DIR}/artifacts/cerebellum_plastic_base.hdf5


# Install bullet muscle simulation
RUN git clone https://github.com/near-nes/bullet_muscle_sim.git $BULLET_MUSCLE_DIR \
    && git clone https://github.com/near-nes/embodiment_sdf_models.git $SDF_MODELS_DIR



RUN git clone https://github.com/near-nes/cerebellar-models $CEREBELLUM_PATH \
    && cd $CEREBELLUM_PATH \
    && git checkout 53656eea5c5dd671371ff3b4f1ac0be9cadf32e9\
    && cd custom_stdp \
    && cmake . \
    && make \
    && make install


WORKDIR ${DEPS_DIR}
COPY ./docker/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

ENV PYTHON_MAJOR_MINOR="python${PYTHON_MAJOR}.${PYTHON_MINOR}"

RUN echo ${NEST_INSTALL_DIR}/lib/${PYTHON_MAJOR_MINOR}/site-packages >> ${VIRTUAL_ENV}/lib/${PYTHON_MAJOR_MINOR}/site-packages/nest.pth


# COPY scripts/interactive_start.py /usr/local/bin/run_interactive.py
# RUN chmod +x /usr/local/bin/run_interactive.py


ENV PYTHONPATH="${CONTROLLER_DIR}:${BULLET_MUSCLE_DIR}:${CEREBELLUM_PATH}${PYTHONPATH:+:${PYTHONPATH}}"
RUN echo "Constructed PYTHONPATH: ${PYTHONPATH}"

WORKDIR /sim

# RUN echo "Setting ownership of shared folders to: >>>>>>>>>>>>>>>>>>> userid:$USER_UID groupid:$USER_GID >>>>>>>>>>>>>>>>>>>"
# RUN chown -R $USERNAME:$USERNAME $VIRTUAL_ENV /home/$USERNAME $SHARED_DATA_DIR $NEST_MODULE_PATH $BULLET_MUSCLE_DIR


# Expose VNC port (Display :1 is 5901)
EXPOSE 5901
ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]

# FROM docker-registry.ebrains.eu/neurorobotics/nrp/nrp-core/nrp-vanilla-ubuntu20:latest AS nrp-image

# FROM runtime AS nrp-runtime
# ENV NRP_HOME=/home/nrpuser/.local/
# ENV NRP_INSTALL_DIR=${NRP_HOME}/nrp
# ENV NRP_DEPS_INSTALL_DIR=${NRP_HOME}/nrp_deps

# RUN mkdir -p $NRP_HOME && chown $USERNAME:$USERNAME $NRP_HOME
# RUN mkdir -p $INSTALL_DIR/nrp $DEPS_DIR/nrp_deps \
#         && chown $USERNAME:$USERNAME $INSTALL_DIR/nrp \
#         && chown $USERNAME:$USERNAME $DEPS_DIR/nrp_deps

# USER $USERNAME

# COPY --chown=$USERNAME:$USERNAME --from=nrp-image /home/nrpuser/.local/nrp/ $INSTALL_DIR/nrp/
# COPY --chown=$USERNAME:$USERNAME --from=nrp-image /home/nrpuser/.local/nrp_deps/ $DEPS_DIR/nrp_deps/
# RUN ln -sf $INSTALL_DIR/nrp $NRP_INSTALL_DIR
# RUN ln -sf $DEPS_DIR/nrp_deps $NRP_DEPS_INSTALL_DIR
USER 0
COPY ./docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
# >>>>>>>>>> VNC SETUP >>>>>>>>>>>>>>
ARG VNC_PASSWORD="vncpass"
ENV VNC_PASSWORD=${VNC_PASSWORD}
ENV VNC_DISPLAY=":1"
ENV DISPLAY="${VNC_DISPLAY}"
COPY scripts/start-vnc.sh /usr/local/bin/start-vnc.sh
RUN chmod +x /usr/local/bin/start-vnc.sh

RUN mkdir -p /home/simuser/.vnc
COPY scripts/xstartup /home/simuser/.vnc/xstartup
RUN chmod 700 /home/$USERNAME/.vnc/xstartup

COPY scripts/aliases.sh /tmp/aliases.sh
RUN cat /tmp/aliases.sh >> /etc/bash.bashrc && rm /tmp/aliases.sh
# Set display for terminals opened in VNC
RUN echo "export DISPLAY=${VNC_DISPLAY}" >> /etc/bash.bashrc

# FROM nrp-runtime AS dev
FROM runtime AS dev
# In dev, the controller directory is mounted from the host and the user is the same as the host user.
ENV SIMULATION_MODE=dev

FROM runtime AS hpc
# In HPC, the controller directory is copied into the image and the user is the default simuser.
ENV SIMULATION_MODE=hpc
COPY . /sim/controller
RUN chown -R simuser:simuser /sim/controller