from pathlib import Path

import structlog
from mpi4py.MPI import Comm
from neural.population_view import PopView

_log: structlog.stdlib.BoundLogger = structlog.get_logger(str(__file__))


def collapse_files(dir: Path, pops: list[PopView], comm: Comm = None):
    """
    Collapses multiple ASCII recording files from different processes into single files per population.
    TODO decide how to handle non-ascii popviews: fail or ignore?
    Parameters
    ----------
    dir : str
        Directory path containing the recording files
    pops : list[PopView]
    comm : Comm
        Comm on which to barrier() on
    Notes
    -----
    Files are processed only by rank 0 process. For each population, files starting with
    the population name are combined, duplicates are removed, and original files are deleted.
    """
    if comm.rank == 0:
        for pop in pops:
            name = pop.label
            file_list = [i for i in dir.iterdir() if i.name.startswith(name)]
            senders = []
            times = []
            combined_data = []

            for f in file_list:
                with open(dir / f, "r") as fd:
                    lines = fd.readlines()
                    for line in lines:
                        if line.startswith("#") or line.startswith("sender"):
                            continue
                        combined_data.append(line.strip())
            unique_lines = list(set(combined_data))

            for line in unique_lines:
                sender, time = line.split()
                senders.append(int(sender))
                times.append(float(time))

            complete_file = dir / (name + ".gdf")
            with open(complete_file, "a") as wfd:
                wfd.write("sender\ttime_ms\n")
                for line in unique_lines:
                    wfd.write(line + "\n")
            pop.filepath = complete_file
            for f in file_list:
                f.unlink()

    comm.barrier()
