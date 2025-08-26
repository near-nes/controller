#!/bin/bash
. /etc/profile

# this entrypoint script does NOT include defaults. it expects env vars to be set by the container, 
# and should error out if they aren't

echo "Running entrypoint..."

# --- Configuration ---
# Directory mounted from host, whose ownership we need to match primarily
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

# --- UID/GID Synchronization ---
SIMULATION_MODE="${SIMULATION_MODE}"

if [ "$SIMULATION_MODE" = "dev" ]; then
    echo "Running in 'dev' mode. Synchronizing UID/GID..."

    # CRITICAL CHECK: Ensure the target directory (bind mount) exists
    if [ ! -d "$TARGET_DIR" ]; then
        echo "Error: Target directory $TARGET_DIR not found or not a directory." >&2
        echo "This directory must be bind-mounted from the host for dev mode." >&2
        exit 1
    fi

    # Get UID and GID of the target directory (mounted from host)
    DIR_UID=$(stat -c "%u" "$TARGET_DIR")
    DIR_GID=$(stat -c "%g" "$TARGET_DIR")
    echo "Mounted directory $TARGET_DIR owned by UID: $DIR_UID, GID: $DIR_GID"

    # Get current container user's UID and GID
    CURRENT_UID=$(id -u "$USERNAME")
    CURRENT_GID=$(id -g "$USERNAME")

    # If UID/GID don't match the directory, change the container user's UID/GID
    if [ "$CURRENT_UID" != "$DIR_UID" ] || [ "$CURRENT_GID" != "$DIR_GID" ]; then
        echo "Current $USERNAME UID/GID ($CURRENT_UID/$CURRENT_GID) differs from target ($DIR_UID/$DIR_GID). Adjusting..."

        # Ensure the target GID exists or modify the existing group
        if ! getent group "$DIR_GID" > /dev/null; then
            echo "Modifying group $USERNAME to GID $DIR_GID..."
            groupmod -o -g "$DIR_GID" "$USERNAME"
        else
            EXISTING_GROUP_NAME=$(getent group "$DIR_GID" | cut -d: -f1)
            if [ "$EXISTING_GROUP_NAME" != "$USERNAME" ]; then
                 echo "Target GID $DIR_GID exists with name $EXISTING_GROUP_NAME. Modifying $USERNAME's primary group GID to $DIR_GID."
                 if id -G "$USERNAME" | grep -qw "$DIR_GID"; then
                     usermod -g "$DIR_GID" "$USERNAME"
                 else
                     groupmod -o -g "$DIR_GID" "$USERNAME"
                 fi
            fi
        fi

        # Modify User: Change the user's UID
        echo "Modifying user $USERNAME to UID $DIR_UID..."
        usermod -o -u "$DIR_UID" "$USERNAME"

        # Adjust ownership of internal directories
        echo "Adjusting ownership of internal directories..."
        chown -R "$DIR_UID:$DIR_GID" "$VENV_PATH" "/home/$USERNAME" "$SHARED_DATA_DIR" "$NEST_MODULE_PATH"

        echo "$USERNAME user adjusted to UID: $DIR_UID, GID: $DIR_GID"
    else
        echo "$USERNAME UID/GID ($CURRENT_UID/$CURRENT_GID) matches target ($DIR_UID/$DIR_GID). No changes needed."
    fi
    USER_ID_TO_USE=$DIR_UID
    GROUP_ID_TO_USE=$DIR_GID
else
    echo "Running in 'hpc' mode. Skipping UID/GID synchronization."
    # In HPC mode, we use the default user and group IDs from the image build
    USER_ID_TO_USE=$(id -u "$USERNAME")
    GROUP_ID_TO_USE=$(id -g "$USERNAME")
fi

# --- Decompress BSB Network File if necessary ---
echo "Checking for BSB network file: ${BSB_NETWORK_FILE}"
if [ ! -f "${BSB_NETWORK_FILE}" ]; then
    echo "Uncompressed network file ${BSB_NETWORK_FILE} not found."
    mkdir -p "$(dirname "${BSB_NETWORK_FILE}")" # Ensure parent directory exists
    echo "Found compressed file ${COMPRESSED_BSB_NETWORK_FILE}. Decompressing..."
    gzip -d -c "${COMPRESSED_BSB_NETWORK_FILE}" > "${BSB_NETWORK_FILE}"
    echo "moving ownership to current user.."
    chown -R "$USER_ID_TO_USE:$GROUP_ID_TO_USE" $BSB_NETWORK_FILE
    echo "ownership changed"
else
    echo "Uncompressed network file ${BSB_NETWORK_FILE} already exists. Skipping decompression."
fi

# --- Set Environment Variables for Final Command ---
# Ensure these are set *before* gosu executes the final command
# so they are inherited by the user's environment.

echo "Final LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "Final PATH: $PATH"
echo "Final PYTHONPATH: $PYTHONPATH"

# --- Execute the command directly if in HPC mode ---
if [ "$SIMULATION_MODE" = "hpc" ]; then
    exec "$@"
fi


# --- Prerequisite Scripts ---
# Start VNC in the background AS THE USER first using the dedicated script.
echo "Entrypoint: Launching VNC background process via gosu..."
# Export variables needed by the background script
export VNC_DISPLAY VNC_PASSWORD HOME=/home/$USERNAME
gosu "$USERNAME" /usr/local/bin/start-vnc.sh

echo "Entrypoint: Executing custom command as user '$USERNAME': $@"

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
exec gosu "$USERNAME" "$@"
# exec gosu "$USERNAME" bash -c 'run_as_user "$@"' bash "$@"
# python controller/complete_control/brain.py
# bash --rcfile <(python controller/complete_control/brain.py)