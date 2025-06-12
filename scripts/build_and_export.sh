#!/bin/bash
set -ex

# --- Configuration ---
IMAGE_NAME="nearnes/controller"
DEFAULT_TAG="hpc-latest"
TAG=${1:-$DEFAULT_TAG} # Use the first argument as a tag, or default to 'hpc-latest'
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"
TAR_FILE="${IMAGE_NAME//\//-}-${TAG}.tar"
GZ_FILE="${TAR_FILE}.gz"

echo "================================================="
echo "Building and exporting HPC image"
echo "Image name: ${FULL_IMAGE_NAME}"
echo "Output file: ${GZ_FILE}"
echo "================================================="

# --- Build ---
echo
echo ">>> Building HPC image: ${FULL_IMAGE_NAME}"
docker build -f docker/Dockerfile --target hpc -t "${FULL_IMAGE_NAME}" .

# --- Save ---
echo
echo ">>> Saving image to TAR archive: ${TAR_FILE}"
docker save -o "${TAR_FILE}" "${FULL_IMAGE_NAME}"

# --- Compress ---
echo
echo ">>> Compressing TAR archive to: ${GZ_FILE}"
gzip -f "${TAR_FILE}"

# --- Final Info ---
echo
echo ">>> Build and export complete!"
echo "To load on another machine, transfer ${GZ_FILE} and run:"
echo "gunzip ${GZ_FILE}"
echo "docker load -i ${TAR_FILE}"