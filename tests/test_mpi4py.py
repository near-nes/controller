"""Smoke tests for mpi4py against the container's custom OpenMPI build.

mpi4py is sensitive to build-time MPI version, compiler flags, and runtime
library paths; these tests catch the common breakage modes:
  1. mpi4py imports and reports Open MPI
  2. Its compiled extension links against ${OMPI_INSTALL_DIR}, not a stray
     system copy from apt
  3. A real multi-rank job runs end-to-end (mpirun spawns ranks, they exchange
     data via collectives, all exit 0)
"""

import os
import shutil
import subprocess
import sys
from textwrap import dedent

import pytest


def test_mpi4py_reports_open_mpi():
    from mpi4py import MPI

    version = MPI.Get_library_version()
    assert "Open MPI" in version, f"expected Open MPI, got: {version!r}"


def test_mpi4py_extension_links_against_custom_ompi():
    import mpi4py.MPI as m

    ompi_install = os.environ.get("OMPI_INSTALL_DIR", "/sim/install/openmpi")
    ldd = subprocess.run(
        ["ldd", m.__file__], capture_output=True, text=True, check=True
    ).stdout

    libmpi_lines = [line for line in ldd.splitlines() if "libmpi.so" in line]
    assert libmpi_lines, f"libmpi.so missing from ldd output:\n{ldd}"
    for line in libmpi_lines:
        assert (
            ompi_install in line
        ), f"mpi4py links to an MPI outside {ompi_install}:\n{line}"


@pytest.mark.skipif(shutil.which("mpirun") is None, reason="mpirun not on PATH")
def test_mpi4py_multi_rank_collectives(tmp_path):
    script = tmp_path / "mpi_job.py"
    script.write_text(dedent("""
        from mpi4py import MPI

        comm = MPI.COMM_WORLD
        rank, size = comm.Get_rank(), comm.Get_size()

        payload = comm.bcast({"magic": 42} if rank == 0 else None, root=0)
        assert payload == {"magic": 42}, payload

        total = comm.allreduce(rank, op=MPI.SUM)
        assert total == size * (size - 1) // 2, (total, size)

        print(f"OK rank={rank}/{size}")
    """))

    env = os.environ.copy()
    # Harmless for non-root; required if someone runs tests as root.
    env.setdefault("OMPI_ALLOW_RUN_AS_ROOT", "1")
    env.setdefault("OMPI_ALLOW_RUN_AS_ROOT_CONFIRM", "1")

    result = subprocess.run(
        ["mpirun", "-np", "2", sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert result.returncode == 0, (
        f"mpirun failed (rc={result.returncode})\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    ok_lines = [l for l in result.stdout.splitlines() if l.startswith("OK rank=")]
    assert (
        len(ok_lines) == 2
    ), f"expected 2 OK lines, got {len(ok_lines)}:\n{result.stdout}"
