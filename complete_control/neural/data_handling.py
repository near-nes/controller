from pathlib import Path

import numpy as np
import structlog
from mpi4py.MPI import Comm
from neural.neural_models import PopulationSpikes, SynapseBlock, SynapseRecording
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
    if comm is None or comm.rank == 0:
        for pop in pops:
            name = pop.label
            file_list = [
                i
                for i in dir.iterdir()
                if i.name.startswith(name) and i.suffix != ".json"
            ]
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

            gids = pop.pop.get("global_id")
            neuron_model = pop.pop.get("model")
            if isinstance(neuron_model, tuple) and len(neuron_model) > 0:
                neuron_model = neuron_model[0]

            pop_spikes = PopulationSpikes(
                label=name,
                gids=np.array(gids),
                senders=np.array(senders),
                times=np.array(times),
                population_size=len(pop.pop),
                neuron_model=neuron_model,
            )

            complete_file = dir / (name + ".json")
            with open(complete_file, "w") as wfd:
                wfd.write(pop_spikes.model_dump_json(indent=4))

            pop.filepath = complete_file
            for f in file_list:
                f.unlink()
    if comm is not None:
        comm.barrier()


def save_conn_weights(weights_history: dict, dir: Path, filename_prefix: str):
    """
    merge SynapseRecording objects with the same (source, target, type, trials_recorded),
    concatenate their weight_history, and save as a JSON array.
    """
    for (source_pop, target_pop), inner in weights_history.items():
        label = f"{source_pop.label}>{target_pop.label}"
        recs = []
        for (
            (source_neur, target_neur, synapse_id, synapse_model),
            weights,
        ) in inner.items():
            recs.append(
                SynapseRecording(
                    source=source_neur,
                    target=target_neur,
                    syn_id=synapse_id,
                    syn_type=synapse_model,
                    weight_history=weights,
                )
            )
        s = SynapseBlock(
            source_pop_label=source_pop.label,
            target_pop_label=target_pop.label,
            synapse_recordings=recs,
        )
        rec_path = dir / f"{filename_prefix}-{label}.json"
        with open(rec_path, "w") as f:
            json_array = s.model_dump_json(indent=2)
            f.write(json_array)
