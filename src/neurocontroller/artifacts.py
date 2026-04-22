"""Resolve the compiled BSB cerebellum network HDF5.

The compressed network is shipped as package data (mouse_abstract_only.hdf5.gz).
On first use it is decompressed once to the user's OS cache directory and the
path is returned on every subsequent call.

Set ``BSB_NETWORK_FILE`` to skip all of this and point directly at an existing
decompressed file.
"""

from __future__ import annotations

import gzip
import os
import shutil
import tempfile
from importlib.resources import files
from pathlib import Path

_GZ_NAME = "artifacts/mouse_abstract_only.hdf5.gz"
_HDF5_NAME = "mouse_abstract_only.hdf5"


def _cache_dir() -> Path:
    try:
        from platformdirs import user_cache_dir

        return Path(user_cache_dir("neurocontroller"))
    except ImportError:
        import tempfile

        return Path(tempfile.gettempdir()) / "neurocontroller"


def get_network_file() -> Path:
    """Return the path to the decompressed BSB network HDF5.

    Checks ``BSB_NETWORK_FILE`` first; if unset, decompresses the bundled
    .gz into the OS cache dir on first call and returns that path.
    """
    override = os.environ.get("BSB_NETWORK_FILE")
    if override:
        return Path(override)

    dest = _cache_dir() / _HDF5_NAME
    if dest.exists():
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    gz_data = files("neurocontroller").joinpath(_GZ_NAME)
    # Decompress to a tmp sibling, then atomically rename. If two processes race,
    # each writes to its own tmp and the losing rename just replaces the winner's
    # byte-identical file; no reader ever sees a partially-written dest.
    tmp_fd, tmp_str = tempfile.mkstemp(
        dir=dest.parent, prefix=_HDF5_NAME + ".", suffix=".tmp"
    )
    tmp_path = Path(tmp_str)
    try:
        with os.fdopen(tmp_fd, "wb") as f_out:
            with gz_data.open("rb") as f_in, gzip.open(f_in) as gz_in:
                shutil.copyfileobj(gz_in, f_out)
        os.replace(tmp_path, dest)
    finally:
        tmp_path.unlink(missing_ok=True)

    return dest
