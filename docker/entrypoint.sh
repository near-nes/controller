#!/bin/bash
. /etc/profile

# This entrypoint runs as root (USER 0). It remaps simuser's UID/GID to match
# the host, then drops to simuser via gosu. Install dirs are world-readable
# from the build, so only small writable dirs need chown.

echo "Running entrypoint..."

# --- Configuration ---
TARGET_DIR="${CONTROLLER_DIR}"
CEREBELLUM_PATH="${CEREBELLUM_PATH}"
SHARED_DATA_DIR="${SHARED_DATA_DIR}"
USERNAME="${USERNAME}"
VENV_PATH="${VIRTUAL_ENV}"
NEST_MODULE_PATH="${NEST_MODULE_PATH}"
COMPRESSED_BSB_NETWORK_FILE="${COMPRESSED_BSB_NETWORK_FILE}"
BSB_NETWORK_FILE="${BSB_NETWORK_FILE}"
NEST_SERVER_BIN="${NEST_INSTALL_DIR}/bin/nest-server"
NEST_SERVER_MPI_BIN="${NEST_INSTALL_DIR}/bin/nest-server-mpi"

PYTHON_MAJOR_MINOR=$(python -c "import sys; print(f'python{sys.version_info.major}.{sys.version_info.minor}')")
SITE_PACKAGES_PATH="$VENV_PATH/lib/${PYTHON_MAJOR_MINOR}/site-packages"

# --- UID/GID Validation ---
SIMULATION_MODE="${SIMULATION_MODE}"

if [ "$SIMULATION_MODE" = "dev" ]; then
    if [ -z "$UID" ] || [ -z "$GID" ]; then
        echo "ERROR: UID and GID environment variables are required." >&2
        echo "  Create a .env file: echo \"UID=\$(id -u)\" >> .env && echo \"GID=\$(id -g)\" >> .env" >&2
        exit 1
    fi

    echo "Running in 'dev' mode. Synchronizing UID/GID..."

    TARGET_UID="$UID"
    TARGET_GID="$GID"

    # Get current container user's UID and GID
    CURRENT_UID=$(id -u "$USERNAME")
    CURRENT_GID=$(id -g "$USERNAME")

    if [ "$CURRENT_UID" != "$TARGET_UID" ] || [ "$CURRENT_GID" != "$TARGET_GID" ]; then
        echo "Current $USERNAME UID/GID ($CURRENT_UID/$CURRENT_GID) differs from target ($TARGET_UID/$TARGET_GID). Adjusting..."

        # Handle GID: check if target GID already exists
        if ! getent group "$TARGET_GID" > /dev/null; then
            groupmod -o -g "$TARGET_GID" "$USERNAME"
        else
            EXISTING_GROUP_NAME=$(getent group "$TARGET_GID" | cut -d: -f1)
            if [ "$EXISTING_GROUP_NAME" != "$USERNAME" ]; then
                echo "Target GID $TARGET_GID exists as group '$EXISTING_GROUP_NAME'. Adding $USERNAME to it."
                usermod -g "$TARGET_GID" "$USERNAME"
            fi
        fi

        # Modify UID
        usermod -o -u "$TARGET_UID" "$USERNAME"

        # install dirs are world-readable, venv is world-writable
        chown -R "$TARGET_UID:$TARGET_GID" "/home/$USERNAME" "$SHARED_DATA_DIR"

        echo "$USERNAME adjusted to UID: $TARGET_UID, GID: $TARGET_GID"
    else
        echo "$USERNAME UID/GID ($CURRENT_UID/$CURRENT_GID) already matches target. No changes needed."
    fi
    USER_ID_TO_USE=$TARGET_UID
    GROUP_ID_TO_USE=$TARGET_GID
else
    echo "Running in 'hpc' mode. Skipping UID/GID synchronization."
    USER_ID_TO_USE=$(id -u "$USERNAME")
    GROUP_ID_TO_USE=$(id -g "$USERNAME")
fi

# --- Decompress BSB Network File if necessary ---
echo "Checking for BSB network file: ${BSB_NETWORK_FILE}"
if [ ! -f "${BSB_NETWORK_FILE}" ]; then
    echo "Uncompressed network file ${BSB_NETWORK_FILE} not found."
    mkdir -p "$(dirname "${BSB_NETWORK_FILE}")"
    echo "Found compressed file ${COMPRESSED_BSB_NETWORK_FILE}. Decompressing..."
    gzip -d -c "${COMPRESSED_BSB_NETWORK_FILE}" > "${BSB_NETWORK_FILE}"
    chown "$USER_ID_TO_USE:$GROUP_ID_TO_USE" "$BSB_NETWORK_FILE"
    echo "Decompression complete."
else
    echo "Uncompressed network file ${BSB_NETWORK_FILE} already exists. Skipping decompression."
fi

# --- Environment Summary ---
echo "Final LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "Final PATH: $PATH"
echo "Final PYTHONPATH: $PYTHONPATH"

# --- Execute the command directly if in HPC mode ---
if [ "$SIMULATION_MODE" = "hpc" ]; then
    exec "$@"
fi

# --- VNC (optional) ---
if [ "${ENABLE_VNC:-false}" = "true" ]; then
    echo "Entrypoint: Launching VNC background process via gosu..."
    export VNC_DISPLAY VNC_PASSWORD HOME=/home/$USERNAME
    gosu "$USERNAME" /usr/local/bin/start-vnc.sh
fi

echo "----------------------------------------"
echo "Switching to user $USERNAME (UID: $USER_ID_TO_USE, GID: $GROUP_ID_TO_USE) and executing command: $@"
echo "----------------------------------------"

if [ "$NEST_MODE" = "nest-server" ]; then
    export NEST_SERVER_HOST="${NEST_SERVER_HOST:-0.0.0.0}"
    export NEST_SERVER_PORT="${NEST_SERVER_PORT:-9000}"
    export NEST_SERVER_STDOUT="${NEST_SERVER_STDOUT:-1}"

    export NEST_SERVER_ACCESS_TOKEN="${NEST_SERVER_ACCESS_TOKEN}"
    export NEST_SERVER_CORS_ORIGINS="${NEST_SERVER_CORS_ORIGINS:-*}"
    export NEST_SERVER_DISABLE_AUTH="${NEST_SERVER_DISABLE_AUTH:-1}"
    export NEST_SERVER_DISABLE_RESTRICTION="${NEST_SERVER_DISABLE_RESTRICTION:-1}"
    export NEST_SERVER_ENABLE_EXEC_CALL="${NEST_SERVER_ENABLE_EXEC_CALL:-1}"
    export NEST_SERVER_MODULES="${NEST_SERVER_MODULES:-import nest; import numpy; import os; import json; import sys}"
    echo "Running nest-server: $NEST_SERVER_BIN"
    exec $NEST_SERVER_BIN start
elif [[ "${MODE}" = 'nest-server-mpi' ]]; then
    export NEST_SERVER_HOST="${NEST_SERVER_HOST:-0.0.0.0}"
    export NEST_SERVER_PORT="${NEST_SERVER_PORT:-52425}"

    export NEST_SERVER_ACCESS_TOKEN="${NEST_SERVER_ACCESS_TOKEN}"
    export NEST_SERVER_CORS_ORIGINS="${NEST_SERVER_CORS_ORIGINS:-*}"
    export NEST_SERVER_DISABLE_AUTH="${NEST_SERVER_DISABLE_AUTH:-1}"
    export NEST_SERVER_DISABLE_RESTRICTION="${NEST_SERVER_DISABLE_RESTRICTION:-1}"
    export NEST_SERVER_ENABLE_EXEC_CALL="${NEST_SERVER_ENABLE_EXEC_CALL:-1}"
    export NEST_SERVER_MODULES="${NEST_SERVER_MODULES:-import nest; import numpy; import numpy as np}"
    export NEST_SERVER_MPI_LOGGER_LEVEL="${NEST_SERVER_MPI_LOGGER_LEVEL:-INFO}"

    export OMPI_ALLOW_RUN_AS_ROOT="${OMPI_ALLOW_RUN_AS_ROOT:-1}"
    export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM="${OMPI_ALLOW_RUN_AS_ROOT_CONFIRM:-1}"
    # exec mpirun -np "${NEST_SERVER_MPI_NUM:-1}" nest-server-mpi --host "${NEST_SERVER_HOST}" --port "${NEST_SERVER_PORT}"
    echo "Running nest-server-mpi: $NEST_SERVER_MPI_BIN"
    exec "${NEST_SERVER_MPI_BIN}" --host "${NEST_SERVER_HOST}" --port "${NEST_SERVER_PORT}"
else
    echo "Running passed command: $@"
    exec gosu "$USERNAME" "$@"
fi
