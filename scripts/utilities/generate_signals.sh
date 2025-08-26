#!/bin/bash
set -euo pipefail # Exit on error, unset var, pipe failure

# --- Configuration & Validation ---

# Check required environment variables
: "${CONTROLLER_DIR:?Error: CONTROLLER_DIR environment variable is not set}"

# Define the target directory where files and the script reside
TARGET_DIR="${CONTROLLER_DIR}/complete_control"

# Define the target files to check/generate
TRAJECTORY_FILE="${TARGET_DIR}/trajectory.txt"
MOTOR_COMMANDS_FILE="${TARGET_DIR}/motor_commands.txt"

# Define the Python script to run (relative path after cd)
PYTHON_SCRIPT_RELATIVE="generate_analog_signals.py"
PYTHON_SCRIPT_FULL="${TARGET_DIR}/${PYTHON_SCRIPT_RELATIVE}"

# Validate that the target directory exists
if [ ! -d "${TARGET_DIR}" ]; then
   echo "Error: Target directory not found: ${TARGET_DIR}" >&2
   exit 1
fi

# Validate that the Python script exists
if [ ! -f "${PYTHON_SCRIPT_FULL}" ]; then
   echo "Error: Python script not found: ${PYTHON_SCRIPT_FULL}" >&2
   exit 1
fi

# --- Check Existing Files & Confirmation ---

# Flag to indicate if regeneration should proceed
PROCEED_GENERATION=true

# Check if either target file already exists
if [ -f "${TRAJECTORY_FILE}" ] || [ -f "${MOTOR_COMMANDS_FILE}" ]; then
    echo "---------------------------------------------------------------------"
    echo "Warning: One or both target files exist in ${TARGET_DIR}:"
    [ -f "${TRAJECTORY_FILE}" ] && echo " - ${TRAJECTORY_FILE}"
    [ -f "${MOTOR_COMMANDS_FILE}" ] && echo " - ${MOTOR_COMMANDS_FILE}"
    echo
    # Use read with -r to handle backslashes, -p for prompt, default to 'n'
    read -r -p "Do you want to regenerate them (existing files will be overwritten)? (y/N): " confirm
    if [[ "$(echo "${confirm:-n}" | tr '[:upper:]' '[:lower:]')" != "y" ]]; then
        echo "Aborting signal generation as regeneration was not confirmed."
        echo "---------------------------------------------------------------------"
        PROCEED_GENERATION=false
        exit 0 # Graceful exit, not an error
    fi
    echo "---------------------------------------------------------------------"
else
    echo "Target signal files do not exist. Proceeding with generation."
fi

# --- Generate Signals ---

if [ "$PROCEED_GENERATION" = true ]; then
    echo "Changing directory to ${TARGET_DIR}"
    cd "${TARGET_DIR}" || { echo "Error: Failed to change directory to ${TARGET_DIR}" >&2; exit 1; }
    echo "Current directory: $(pwd)"

    echo "---------------------------------------------------------------------"
    echo "Running Python script to generate signals: ${PYTHON_SCRIPT_RELATIVE}"
    echo "---------------------------------------------------------------------"

    # Execute the python script
    python3 "${PYTHON_SCRIPT_RELATIVE}"

    # Script exits here if python3 fails (due to set -e)

    # --- Completion Message ---
    echo "---------------------------------------------------------------------"
    echo "Python script finished successfully."
    echo "Generated/Updated files:"
    echo " - trajectory.txt"
    echo " - motor_commands.txt"
    echo "in directory: ${TARGET_DIR}"
    echo "---------------------------------------------------------------------"
else
    # This part should theoretically not be reached due to exit 0 above,
    # but added for logical completeness.
    echo "Signal generation skipped."
fi

exit 0