#!/bin/bash
set -euo pipefail # Exit on error, unset var, pipe failure

# --- Configuration & Validation ---

# Build directory (absolute path)
BUILD_DIR="/sim/controller/built_custom_stdp"

# Check required environment variables
: "${CONTROLLER_DIR:?Error: CONTROLLER_DIR environment variable is not set}"
: "${NEST_INSTALL_DIR:?Error: NEST_INSTALL_DIR environment variable is not set (needed for cmake)}"

# Source directory for the custom module
SOURCE_DIR="${CONTROLLER_DIR}/cerebellum/custom_stdp"

# Validate that the source directory exists
if [ ! -d "${SOURCE_DIR}" ]; then
   echo "Error: Source directory for custom_stdp not found: ${SOURCE_DIR}" >&2
   exit 1
fi

# --- Preparation ---
echo "Ensuring build directory exists: ${BUILD_DIR}"
# Create the build directory if it doesn't exist. Does nothing if it exists.
mkdir -p "${BUILD_DIR}" || { echo "Error: Failed to create directory ${BUILD_DIR}" >&2; exit 1; }

# --- Check Contents & Determine Action ---

PERFORM_FULL_BUILD=true # Default action assumes empty dir or user confirmation

# Check if the directory contains any files or directories (excluding . and ..)
# The '-A' flag includes hidden files/dirs except . and ..
if [ -n "$(ls -A "${BUILD_DIR}")" ]; then
    echo "---------------------------------------------------------------------"
    echo "Warning: Build directory '${BUILD_DIR}' is not empty."
    echo "This usually means previous build files exist."
    # Use read with -r to handle backslashes, -p for prompt, default to 'n'
    read -r -p "Do you want to clear contents and rebuild (y), or just reinstall (N)? (y/N): " confirm
    CHOICE=$(echo "${confirm:-n}" | tr '[:upper:]' '[:lower:]') # Default to 'n', convert to lowercase
    echo "---------------------------------------------------------------------"

    if [[ "$CHOICE" == "y" ]]; then
        PERFORM_FULL_BUILD=true
        echo "Clearing contents of ${BUILD_DIR} for full rebuild..."
        # Use find to delete all contents (files, directories, hidden) within the directory
        find "${BUILD_DIR}" -mindepth 1 -delete || { echo "Error: Failed to clear contents of ${BUILD_DIR}" >&2; exit 1; }
        echo "Directory contents cleared."
    else
        # User chose 'n' or entered something invalid (defaulting to 'n')
        PERFORM_FULL_BUILD=false
        echo "Skipping clear, CMake, and make. Proceeding directly to reinstall..."
    fi
else
    echo "Build directory is empty or contains only '.' and '..'."
    echo "Proceeding with full build and install."
    PERFORM_FULL_BUILD=true # Explicitly set, although it's the default
fi

# --- Build / Install ---
NEST_BIN=$NEST_INSTALL_DIR/bin/nest-config
echo "---------------------------------------------------------------------"
if [ "$PERFORM_FULL_BUILD" = true ]; then
    echo "Starting full build process: CMake, Make, and Make Install..."
else
    echo "Starting reinstall process: Make Install only..."
fi
echo "Build directory: ${BUILD_DIR}"
echo "Source directory: ${SOURCE_DIR}"
echo "NEST binary: ${NEST_BIN}"
echo "---------------------------------------------------------------------"

# Change into the build directory is necessary for both cases
echo "Changing directory to ${BUILD_DIR}"
cd "${BUILD_DIR}" || { echo "Error: Failed to change directory to ${BUILD_DIR}" >&2; exit 1; }

# Conditionally run CMake and Make
if [ "$PERFORM_FULL_BUILD" = true ]; then
    # Run CMake
    echo "Running CMake..."
    # Use || { ... } for better error handling than just set -e
    cmake -Dwith-nest="${NEST_BIN}" "${SOURCE_DIR}" || { echo "Error: CMake configuration failed." >&2; exit 1; }

    # Run Make
    echo "Running make..."
    make || { echo "Error: Make build failed." >&2; exit 1; }
fi

# Run Make Install (runs in both cases: after full build or as reinstall only)
echo "Running make install..."
make install || { echo "Error: Make install failed." >&2; exit 1; }

# --- Completion Message ---
# set -e/-u/-o pipefail handles errors, so if we reach here, it succeeded.
echo "---------------------------------------------------------------------"
if [ "$PERFORM_FULL_BUILD" = true ]; then
    echo "Custom STDP module successfully regenerated and installed."
else
    echo "Custom STDP module successfully reinstalled (using existing build files)."
fi
echo "Build directory: ${BUILD_DIR}"
echo "---------------------------------------------------------------------"

exit 0