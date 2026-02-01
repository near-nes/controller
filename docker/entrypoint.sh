#!/bin/bash
. /etc/profile

# This entrypoint script expects UID and GID environment variables to be set.
# See: https://github.com/near-nes/controller/issues/85

echo "Running entrypoint..."

# --- Configuration ---
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
# UID and GID must be provided as environment variables.
# This ensures consistent behavior across all platforms (Linux, macOS, Windows).
if [ -z "$UID" ] || [ -z "$GID" ]; then
    echo "========================================" >&2
    echo "ERROR: UID and GID environment variables are required." >&2
    echo "" >&2
    echo "These variables must be set to match your host user's UID/GID" >&2
    echo "to ensure correct file permissions on mounted volumes." >&2
    echo "" >&2
    echo "Quick fix:" >&2
    echo "  1. Create a .env file in the project root with:" >&2
    echo "       UID=\$(id -u)" >&2
    echo "       GID=\$(id -g)" >&2
    echo "  2. Or run: echo \"UID=\$(id -u)\" >> .env && echo \"GID=\$(id -g)\" >> .env" >&2
    echo "" >&2
    echo "See: https://github.com/near-nes/controller/issues/85" >&2
    echo "========================================" >&2
    exit 1
fi

TARGET_UID="$UID"
TARGET_GID="$GID"
echo "Target UID/GID from environment: $TARGET_UID:$TARGET_GID"

# --- UID/GID Synchronization ---
SIMULATION_MODE="${SIMULATION_MODE}"
echo "Running in '$SIMULATION_MODE' mode..."

# Get current container user's UID and GID
CURRENT_UID=$(id -u "$USERNAME")
CURRENT_GID=$(id -g "$USERNAME")

# If UID/GID don't match, adjust the container user
if [ "$CURRENT_UID" != "$TARGET_UID" ] || [ "$CURRENT_GID" != "$TARGET_GID" ]; then
    echo "Current $USERNAME UID/GID ($CURRENT_UID/$CURRENT_GID) differs from target ($TARGET_UID/$TARGET_GID). Adjusting..."

    # Adjust GID: assign user to existing group or create new one
    if [ "$CURRENT_GID" != "$TARGET_GID" ]; then
        if getent group "$TARGET_GID" > /dev/null; then
            # Target GID exists, just change user's primary group
            EXISTING_GROUP=$(getent group "$TARGET_GID" | cut -d: -f1)
            echo "Using existing group '$EXISTING_GROUP' (GID $TARGET_GID) for $USERNAME"
            usermod -g "$TARGET_GID" "$USERNAME"
        else
            # Target GID doesn't exist, create a new group
            echo "Creating group '$USERNAME' with GID $TARGET_GID"
            groupadd -o -g "$TARGET_GID" "$USERNAME"
            usermod -g "$TARGET_GID" "$USERNAME"
        fi
    fi

    # Adjust UID
    if [ "$CURRENT_UID" != "$TARGET_UID" ]; then
        echo "Modifying user $USERNAME to UID $TARGET_UID..."
        usermod -o -u "$TARGET_UID" "$USERNAME"
    fi

    # Adjust ownership of internal directories
    echo "Adjusting ownership of internal directories..."
    if [ "$SIMULATION_MODE" = "dev" ]; then
        # Dev mode: full chown including venv (for pip install, etc.)
        chown -R "$TARGET_UID:$TARGET_GID" "$VENV_PATH" "/home/$USERNAME" "$SHARED_DATA_DIR" "$NEST_MODULE_PATH"
    else
        # HPC mode: skip venv (read-only), only chown writable directories
        chown -R "$TARGET_UID:$TARGET_GID" "/home/$USERNAME" "$SHARED_DATA_DIR" "$NEST_MODULE_PATH"
    fi

    echo "$USERNAME user adjusted to UID: $TARGET_UID, GID: $TARGET_GID"
else
    echo "$USERNAME UID/GID ($CURRENT_UID/$CURRENT_GID) already matches target. No changes needed."
fi

USER_ID_TO_USE=$TARGET_UID
GROUP_ID_TO_USE=$TARGET_GID

# --- Decompress BSB Network File if necessary ---
echo "Checking for BSB network file: ${BSB_NETWORK_FILE}"
if [ ! -f "${BSB_NETWORK_FILE}" ]; then
    echo "Uncompressed network file ${BSB_NETWORK_FILE} not found."
    mkdir -p "$(dirname "${BSB_NETWORK_FILE}")" # Ensure parent directory exists
    echo "Found compressed file ${COMPRESSED_BSB_NETWORK_FILE}. Decompressing..."
    gzip -d -c "${COMPRESSED_BSB_NETWORK_FILE}" > "${BSB_NETWORK_FILE}"
    echo "moving ownership to current user.."
    chown -R "$USER_ID_TO_USE" $BSB_NETWORK_FILE
    echo "ownership changed"
else
    echo "Uncompressed network file ${BSB_NETWORK_FILE} already exists. Skipping decompression."
fi

# --- Set Environment Variables for Final Command ---
echo "Final LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "Final PATH: $PATH"
echo "Final PYTHONPATH: $PYTHONPATH"

# --- Execute the command directly if in HPC mode ---
if [ "$SIMULATION_MODE" = "hpc" ]; then
    exec gosu "$USERNAME" "$@"
fi


# Start VNC as the user.
echo "Entrypoint: Launching VNC background process via gosu..."
export VNC_DISPLAY VNC_PASSWORD HOME=/home/$USERNAME
gosu "$USERNAME" /usr/local/bin/start-vnc.sh

echo "----------------------------------------"
echo "Switching to user $USERNAME (UID: $USER_ID_TO_USE) and executing command: $@"
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
