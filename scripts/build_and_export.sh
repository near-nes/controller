#!/bin/bash
set -euo pipefail

# --- Configuration ---
IMAGE_NAME="nearnes/controller"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
DEFAULT_TAG="hpc-latest"
TAG=${1:-$DEFAULT_TAG} # Use the first argument as a tag, or default to a timestamped tag.
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"
TAR_FILE="${IMAGE_NAME//\//-}-${TAG}-${TIMESTAMP}.tar"
GZ_FILE="${TAR_FILE}.gz"

echo "================================================="
echo "Building and exporting HPC image"
echo "Image name: ${FULL_IMAGE_NAME}"
echo "Output file: ${GZ_FILE}"
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
echo "du -sh ${TAR_FILE} | cut -f1"
echo
echo ">>> Build and export complete!"
echo "To load on another machine, transfer ${GZ_FILE} and run:"
echo "  gunzip ${GZ_FILE}"
echo "To then build a singularity container out of this:"
echo "  singularity build sim.sif docker-archive://sim.tar"
echo "create necessary folders with:"
echo " mkdir artifacts results scratch"
echo "and run with:"
echo "  mpirun -np 7 singularity exec --bind ./scratch:/scratch_local --bind ./results:/sim/controller/runs --bind ./artifacts:/sim/controller/artifacts sim.sif/ music /sim/controller/complete_control/complete.music"
echo "clone the repo and mount complete_control for code/parameter changes"