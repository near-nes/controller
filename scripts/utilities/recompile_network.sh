#!/bin/bash
set -euo pipefail # Exit on error, unset var, pipe failure

# --- Configuration & Validation ---
# Check CONTROLLER_DIR is set and cerebellum subdir exists
CEREBELLUM_DIR="${CONTROLLER_DIR:?Error: CONTROLLER_DIR environment variable is not set}/cerebellum"
if [ ! -d "${CEREBELLUM_DIR}" ]; then
   echo "Error: Directory ${CEREBELLUM_DIR} not found." >&2
   exit 1
fi

# paths (relative for bsb input, absolute for check/output/log)
BSB_INPUT_YAML_RELATIVE="configurations/mouse/dcn-io/microzones_complete.yaml"
TARGET_HDF5_CHECK="${CEREBELLUM_DIR}/mouse_cereb_microzones_complete.hdf5"
OUTPUT_DIR_BASE="/sim/controller/built_models"
LOG_DIR_BASE="/sim/controller/logs"

# Validate the existence of the specific input YAML required by bsb
BSB_INPUT_YAML_FULL="${CEREBELLUM_DIR}/${BSB_INPUT_YAML_RELATIVE}"
if [ ! -f "${BSB_INPUT_YAML_FULL}" ]; then
    echo "Error: Required input YAML file for bsb not found: ${BSB_INPUT_YAML_FULL}" >&2
    exit 1
fi

# --- Preparation ---
echo "Changing directory to ${CEREBELLUM_DIR}"
cd "${CEREBELLUM_DIR}" || exit 1 # Exit if cd fails

# --- Existence Check & Confirmation ---
if [ -f "${TARGET_HDF5_CHECK}" ]; then
    echo "---------------------------------------------------------------------"
    # Use read with -r to handle backslashes, -p for prompt, default to 'n'
    read -r -p "Previously compiled network '${TARGET_HDF5_CHECK}' exists. Replace? (y/N): " confirm
    if [[ "$(echo "${confirm:-n}" | tr '[:upper:]' '[:lower:]')" == "y" ]]; then
        echo "Deleting existing file: ${TARGET_HDF5_CHECK}"
        rm -f "${TARGET_HDF5_CHECK}" || { echo "Error: Failed to delete ${TARGET_HDF5_CHECK}" >&2; exit 1; }
    else
        echo "Aborting compilation as replacement was not confirmed."
        echo "---------------------------------------------------------------------"
        exit 0 # Graceful exit
    fi
    echo "---------------------------------------------------------------------"
fi

# --- Prepare for Compilation ---
TIMESTAMP=$(date +%F_%T) # Format: YYYY-MM-DD_HH:MM:SS
OUTPUT_HDF5_FILENAME="from_microzones_complete_nest@${TIMESTAMP}.hdf5" # Based on hardcoded input basename
OUTPUT_HDF5_PATH="${OUTPUT_DIR_BASE}/${OUTPUT_HDF5_FILENAME}"
LOG_FILE_PATH="${LOG_DIR_BASE}/${TIMESTAMP}.txt"

# Ensure output and log directories exist
mkdir -p "${OUTPUT_DIR_BASE}" "${LOG_DIR_BASE}" || { echo "Error: Failed to create output/log directories" >&2; exit 1; }

echo "---------------------------------------------------------------------"
echo "Starting BSB compilation..."
echo "Input YAML (for bsb): ${BSB_INPUT_YAML_RELATIVE}"
echo "Output HDF5 File:   ${OUTPUT_HDF5_PATH}"
echo "Log File:           ${LOG_FILE_PATH}"
echo "---------------------------------------------------------------------"

# --- Execute Compilation ---
# Run bsb compile, redirecting stdout & stderr through tee to terminal and log file
bsb compile -v4 -o "${OUTPUT_HDF5_PATH}" "${BSB_INPUT_YAML_RELATIVE}" 2>&1 | tee -a "${LOG_FILE_PATH}"

# Script exits here if bsb fails (due to set -eo pipefail)

# --- Completion Message ---
echo "---------------------------------------------------------------------"
echo "Compilation command finished successfully."
echo "Output *should* written to: ${OUTPUT_HDF5_PATH} but is likely at /sim/controller/cerebellum/mouse_cereb_microzones_complete_nest.hdf5"
echo "Full log available at: ${LOG_FILE_PATH}"
echo "---------------------------------------------------------------------"

exit 0