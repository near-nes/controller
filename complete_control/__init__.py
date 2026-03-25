"""NRP Near-NES Controller Package

This package contains the neural simulation and cerebellar control experiment code.
On first import, it automatically decompresses the BSB cerebellum network file if needed.
"""

import gzip
import logging
from pathlib import Path

__version__ = "0.1.0"
__all__ = ["__version__"]

logger = logging.getLogger(__name__)


def _decompress_bsb_network():
    """
    Decompress cerebellum_plastic_base.hdf5.gz to cerebellum_plastic_base.hdf5 if needed.
    This runs once on first package import to ensure the BSB network file is available.
    """
    try:
        # Get the artifacts directory within this package
        package_dir = Path(__file__).parent.parent  # go up to controller root
        artifacts_dir = package_dir / "artifacts"

        if not artifacts_dir.exists():
            logger.debug(f"Artifacts directory not found at {artifacts_dir}")
            return

        compressed_file = artifacts_dir / "cerebellum_plastic_base.hdf5.gz"
        decompressed_file = artifacts_dir / "cerebellum_plastic_base.hdf5"

        # Skip if already decompressed
        if decompressed_file.exists():
            logger.debug(f"BSB network file already decompressed: {decompressed_file}")
            return

        # Skip if compressed file doesn't exist
        if not compressed_file.exists():
            logger.debug(f"Compressed BSB network file not found: {compressed_file}")
            return

        # Decompress
        logger.info(f"Decompressing BSB network file: {compressed_file}")
        with gzip.open(compressed_file, "rb") as f_in:
            with open(decompressed_file, "wb") as f_out:
                f_out.writelines(f_in)

        logger.info(f"Successfully decompressed to: {decompressed_file}")

    except Exception as e:
        logger.warning(f"Failed to decompress BSB network file: {e}")
        # Don't raise; the file might be needed later or might already exist elsewhere


# Auto-decompress on first import
_decompress_bsb_network()
