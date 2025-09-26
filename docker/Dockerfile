ARG PYTHON_MAJOR=3
ARG PYTHON_MINOR=10

FROM ubuntu:jammy AS base

ARG PYTHON_MAJOR
ARG PYTHON_MINOR

RUN apt-get update && apt-get install -y --no-install-recommends \
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
    xterm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# nrp-core dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg2 \
    software-properties-common \
    sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN add-apt-repository ppa:pistache+team/unstable
RUN apt-get update && apt-get install -y --no-install-recommends \
    libboost-filesystem1.74.0 \
    libboost-python1.74.0 \
    libboost-numpy1.74.0 \
    libbrotli1 \
    libcurl4 \
    libgrpc++1 \
    libpistache0 \
    libprotobuf23 \
    libzip-dev \
    nlohmann-json3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ARG UID=1000
ARG GID=1000
ENV USERNAME=simuser
RUN set -eux; \
    # create group only if GID is not already present
    if ! getent group "$GID" >/dev/null; then \
    groupadd --gid "$GID" "$USERNAME"; \
    fi; \
    useradd --uid "$UID" --gid "$GID" --create-home --shell /bin/bash "$USERNAME"; \
    echo "${USERNAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# RUN groupadd --gid $GID $USERNAME && \
#     useradd --uid $UID --gid $GID --create-home --shell /bin/bash $USERNAME \
#     && echo "${USERNAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN mkdir /sim && chown $USERNAME /sim

USER $USERNAME
ARG PYTHON_MAJOR
ARG PYTHON_MINOR
ENV USERNAME=simuser


WORKDIR /sim
ENV VIRTUAL_ENV=/sim/venv
RUN python -m venv --system-site-packages $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY ./docker/constraints.txt /tmp/constraints.txt
RUN pip install --upgrade pip setuptools wheel packaging -c /tmp/constraints.txt

ENV INSTALL_DIR=/sim/install
ENV DEPS_DIR=/sim/dependencies
ENV NEST_INSTALL_DIR=$INSTALL_DIR/nest
ENV MUSIC_INSTALL_DIR=$INSTALL_DIR/music
ENV OMPI_INSTALL_DIR=$INSTALL_DIR/openmpi

ENV CONTROLLER_DIR=/sim/controller
ENV SHARED_DATA_DIR=/sim/shared_data
ENV NEST_MODULE_PATH=/sim/install/nest/lib/nest
ENV NEST_PYTHON_MODULE_PATH=${NEST_INSTALL_DIR}/lib/python${PYTHON_MAJOR}.${PYTHON_MINOR}/site-packages/nest
RUN mkdir -p $CONTROLLER_DIR $SHARED_DATA_DIR $NEST_MODULE_PATH

ENV CEREBELLUM_PATH=/sim/cerebellum
ENV LD_LIBRARY_PATH="${MUSIC_INSTALL_DIR}/lib"

RUN mkdir -p $INSTALL_DIR $DEPS_DIR $NEST_INSTALL_DIR $MUSIC_INSTALL_DIR

# openmpi, music and nest
FROM base AS builder

RUN sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libtool \
    cmake \
    libgsl-dev \
    libltdl-dev \
    libreadline-dev \
    python3-dev \
    && sudo apt-get clean \
    && sudo rm -rf /var/lib/apt/lists/*

# nrp-core dependencies
RUN sudo apt-get update && sudo apt-get install -y --no-install-recommends \
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
    libpistache-dev \
    && sudo apt-get clean \
    && sudo rm -rf /var/lib/apt/lists/*

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
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install cython mpilock mpi4py -c /tmp/constraints.txt
ENV CFLAGS=

WORKDIR $DEPS_DIR

####################### MUSIC #######################
RUN git clone https://github.com/INCF/MUSIC \
    && cd MUSIC \
    && git checkout 6d12edf7094e1dbb473dd55f6fcbd0825f30b811 \
    && ./autogen.sh \
    && ./configure --prefix=$MUSIC_INSTALL_DIR --with-python=$VIRTUAL_ENV/bin/python \
    && make -j$(nproc) \
    && make install

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


####################### NRP #######################
ENV NRP_INSTALL_DIR=${INSTALL_DIR}/nrp
ENV NRP_DEPS_INSTALL_DIR=${INSTALL_DIR}/nrp_deps

# nrp-core tests dependencies
RUN sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    cppcheck \
    libgmock-dev \
    xvfb
# unclear nrp-core dependencies
RUN sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    pkg-config

# Install MQTT (to NRP_DEPS_INSTALL_DIR)
RUN git clone https://github.com/eclipse/paho.mqtt.cpp \
    && cd paho.mqtt.cpp \
    && git checkout v1.4.0 \
    && git submodule init \
    && git submodule update \
    && cmake -Bbuild -H. -DPAHO_BUILD_STATIC=OFF -DPAHO_BUILD_SHARED=ON -DCMAKE_INSTALL_PREFIX="${NRP_DEPS_INSTALL_DIR}" -DCMAKE_PREFIX_PATH="${NRP_DEPS_INSTALL_DIR}" -DPAHO_WITH_MQTT_C=ON \
    && cmake --build build/ --target install \
    && sudo ldconfig && cd .. && rm -rf paho.mqtt.cpp

COPY ./docker/requirements_nrp.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements_nrp.txt -c /tmp/constraints.txt

ENV NRP_SRC_DIR=/tmp/nrp-core-src
RUN mkdir -p /tmp/nrp-core-src
ENV CMAKE_CACHE_FILE=${NRP_SRC_DIR}/.ci/cmake_cache/t3_4.cmake
# TODO: copy source files more elegant, but without breaking the cache
# Copying the root (.) immediatly breaks the cache
COPY --chown=${USERNAME} nrp-core/src ${NRP_SRC_DIR}/src
COPY --chown=${USERNAME} nrp-core/docs ${NRP_SRC_DIR}/docs
COPY --chown=${USERNAME} nrp-core/examples ${NRP_SRC_DIR}/examples
COPY --chown=${USERNAME} nrp-core/cmake ${NRP_SRC_DIR}/cmake
COPY --chown=${USERNAME} nrp-core/CMakeLists.txt ${NRP_SRC_DIR}/CMakeLists.txt
COPY --chown=${USERNAME} docker/nrp_t3_4.cmake ${CMAKE_CACHE_FILE}
COPY --chown=${USERNAME} nrp-core/.ci/11-prepare-build.sh ${NRP_SRC_DIR}/.ci/11-prepare-build.sh
COPY --chown=${USERNAME} nrp-core/.ci/20-build.sh ${NRP_SRC_DIR}/.ci/20-build.sh

RUN cd ${NRP_SRC_DIR} && ls -al && bash .ci/11-prepare-build.sh && bash .ci/20-build.sh


####################### CEREBELLUM+MODELS #######################
RUN git clone https://github.com/near-nes/cerebellar-models $CEREBELLUM_PATH \
    && cd $CEREBELLUM_PATH \
    && git checkout f538488a988061afad63655cf9e71751a26d2078\
    && cd custom_stdp \
    && cmake . \
    && make \
    && make install

# parallelize slow pip installs    
FROM base AS core_reqs
WORKDIR ${DEPS_DIR}
COPY ./docker/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -c /tmp/constraints.txt

FROM base AS planner_reqs
WORKDIR ${DEPS_DIR}
# split from reqs to download CPU only
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install gle-code -c /tmp/constraints.txt

# final runtime image
FROM base AS runtime

ENV NRP_INSTALL_DIR=${INSTALL_DIR}/nrp
ENV NRP_DEPS_INSTALL_DIR=${INSTALL_DIR}/nrp_deps

ENV PATH="${VIRTUAL_ENV}/bin:${NRP_INSTALL_DIR}/bin:${MUSIC_INSTALL_DIR}/bin:${NEST_INSTALL_DIR}/bin:${OMPI_INSTALL_DIR}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${OMPI_INSTALL_DIR}/lib64:${NRP_INSTALL_DIR}/lib:${NRP_DEPS_INSTALL_DIR}/lib:${LD_LIBRARY_PATH}"

COPY --from=builder ${INSTALL_DIR} ${INSTALL_DIR}
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder ${CEREBELLUM_PATH} ${CEREBELLUM_PATH}
COPY --from=core_reqs ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=planner_reqs ${VIRTUAL_ENV} ${VIRTUAL_ENV}
# openMPI needs this if no ssh/rsh available
ENV OMPI_MCA_plm=^rsh

# suppress nest startup message
ENV PYNEST_QUIET=1

# cerebellum
ENV COMPRESSED_BSB_NETWORK_FILE=${CONTROLLER_DIR}/artifacts/cerebellum_plastic_base.hdf5.gz
ENV BSB_NETWORK_FILE=${CONTROLLER_DIR}/artifacts/cerebellum_plastic_base.hdf5

ENV PYTHON_MAJOR_MINOR="python${PYTHON_MAJOR}.${PYTHON_MINOR}"

# point nest to nest installation
RUN echo ${NEST_INSTALL_DIR}/lib/${PYTHON_MAJOR_MINOR}/site-packages >> ${VIRTUAL_ENV}/lib/${PYTHON_MAJOR_MINOR}/site-packages/nest.pth
# pythonpath construction
ENV PYTHONPATH="${NRP_INSTALL_DIR}/lib/python${PYTHON_MAJOR}.${PYTHON_MINOR}/site-packages:${CONTROLLER_DIR}:${CEREBELLUM_PATH}${PYTHONPATH:+:${PYTHONPATH}}"
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

RUN mkdir -p /home/$USERNAME/.vnc
COPY scripts/services/xstartup /home/$USERNAME/.vnc/xstartup
RUN chmod 700 /home/$USERNAME/.vnc/xstartup
RUN chown -R $USERNAME /home/$USERNAME/.vnc
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
ENV SUBMODULES_PATH=${CONTROLLER_DIR}/submodules
ENV PYTHONPATH="${SUBMODULES_PATH}${PYTHONPATH:+:${PYTHONPATH}}"
ENV SDF_MODELS_DIR=${SUBMODULES_PATH}/embodiment_sdf_models
RUN echo "Constructed PYTHONPATH: ${PYTHONPATH}"

FROM runtime AS hpc
# >>>>>>>tmp, move to git-installable packages asap TODO
ENV SUBMODULES_PATH=${CONTROLLER_DIR}/submodules
ENV PYTHONPATH="${SUBMODULES_PATH}${PYTHONPATH:+:${PYTHONPATH}}"
ENV SDF_MODELS_DIR=${SUBMODULES_PATH}/embodiment_sdf_models
RUN echo "Constructed PYTHONPATH: ${PYTHONPATH}"
# <<<<<<<

# In HPC, the controller directory is copied into the image and the user is the default simuser.
ENV SIMULATION_MODE=hpc
# On HPC do not mount anythin on top of artifacts folder, so that the archive is not overwritten
ENV BSB_NETWORK_FILE=/tmp/cerebellum_plastic_base.hdf5
COPY . /sim/controller
RUN chown -R ${USERNAME} /sim/controller
RUN chmod -R a+rwX /sim
