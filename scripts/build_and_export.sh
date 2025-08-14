#!/bin/bash
set -euo pipefail

# --- Configuration ---
IMAGE_NAME="nearnes/controller"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
DEFAULT_TAG="hpc-latest"

# --- Args ---
# Cases:
# 0 args -> TAG=DEFAULT, no REMOTE
# 1 arg  -> if user@host -> REMOTE; else -> TAG
# 2 args -> TAG then REMOTE (user@host)
TAG="$DEFAULT_TAG"
REMOTE=""

if [[ $# -ge 1 ]]; then
  if [[ "$1" =~ ^[^@[:space:]]+@[^@[:space:]]+$ ]]; then
    REMOTE="$1"
  else
    TAG="$1"
  fi
fi

if [[ $# -ge 2 ]]; then
  REMOTE="$2"
  # Optionally validate format:
  if ! [[ "$REMOTE" =~ ^[^@[:space:]]+@[^@[:space:]]+$ ]]; then
    echo "Error: remote must be in the form <username>@<host>"
    exit 1
  fi
fi

FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"
TAR_FILE="${IMAGE_NAME//\//-}-${TAG}-${TIMESTAMP}.tar"
GZ_FILE="${TAR_FILE}.gz"

echo "================================================="
echo "Building and exporting HPC image"
echo "Image name: ${FULL_IMAGE_NAME}"
echo "Output file: ${GZ_FILE}"
if [[ -n "${REMOTE}" ]]; then
  echo "Remote: ${REMOTE}"
fi
echo "================================================="

# --- Build ---
echo
echo ">>> Building HPC image: ${FULL_IMAGE_NAME}"
docker build -f docker/Dockerfile --target hpc -t "${FULL_IMAGE_NAME}" --progress=plain .

# --- Save ---
echo
echo ">>> Saving image to TAR archive: ${TAR_FILE}"
docker save -o "${TAR_FILE}" "${FULL_IMAGE_NAME}"

# --- Compress ---
echo
echo ">>> Compressing TAR archive to: ${GZ_FILE}"
gzip -f "${TAR_FILE}"

# --- Final Info ---
echo ">>> Final TAR archive size:"
du -sh "${GZ_FILE}" | cut -f1
echo
echo ">>> Build and export complete!"
echo "To load on another machine, transfer ${GZ_FILE} and run:"
echo "  gunzip ${GZ_FILE}"
echo "To then build a singularity container out of this:"
echo "  singularity build sim.sif docker-archive://${TAR_FILE}"
echo "create necessary folders with:"
echo "  mkdir artifacts results scratch"
echo "and run with:"
echo "  mpirun -np 7 singularity exec --bind ./scratch:/scratch_local --bind ./results:/sim/controller/runs --bind ./artifacts:/sim/controller/artifacts sim.sif music /sim/controller/complete_control/complete.music"
echo "clone the repo and mount complete_control for code/parameter changes"

# --- Optional: transfer & build on remote if REMOTE provided ---
if [[ -n "${REMOTE}" ]]; then
  echo
  echo ">>> Copying ${GZ_FILE} to ${REMOTE}:"
  scp -p "${GZ_FILE}" "${REMOTE}:"

  echo
  echo ">>> Running remote extraction and Singularity build on ${REMOTE}:"
  ssh -o BatchMode=yes "${REMOTE}" bash -lc "'
    set -euo pipefail
    echo \"Decompressing ${GZ_FILE}...\"
    gzip -df \"${GZ_FILE}\"

    echo \"Building Singularity image sim.sif from docker-archive://${TAR_FILE} (forcing overwrite if exists)...\"
    singularity build --force sim.sif docker-archive://\"${TAR_FILE}\"

    echo \"Remote Singularity build complete: sim.sif\"
  '"
  echo
  echo ">>> Remote steps completed on ${REMOTE}."
fi
