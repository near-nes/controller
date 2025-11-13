from pathlib import Path
from typing import List

import structlog
from mpi4py.MPI import Comm
from neural.result_models import NeuralResultManifest
from neural.Controller import PopulationBlocks
from neural.nest_adapter import nest
from neural.neural_models import (
    SynapseBlock,
    SynapseRecording,
)

_log: structlog.stdlib.BoundLogger = structlog.get_logger(str(__file__))


def collapse_files(
    dir: Path,
    pop_blocks: PopulationBlocks,
    comm: Comm = None,
):
    """
    Collapses multiple ASCII recording files from different processes into single files per population.
    TODO decide how to handle non-ascii popviews: fail or ignore?
    Parameters
    ----------
    dir : str
        Directory path containing the recording files
    pop_blocks : PopulationBlocks
    comm : Comm
        Comm on which to barrier() on
    Notes
    -----
    Files are processed only by rank 0 process. For each population, files starting with
    the population name are combined, duplicates are removed, and original files are deleted.
    """

    controller_rec = cerebhandler_rec = cereb_rec = None
    use_cerebellum = False

    controller_rec = pop_blocks.controller.to_recording(dir, comm)

    if pop_blocks.cerebellum_handler:
        use_cerebellum = True
        cerebhandler_rec = pop_blocks.cerebellum_handler.to_recording(dir, comm)
        cereb_rec = pop_blocks.cerebellum.to_recording(dir, comm)

    if comm is not None:
        nest.SyncProcesses()

    return NeuralResultManifest(
        controller=controller_rec,
        cerebellum_handler=cerebhandler_rec,
        cerebellum=cereb_rec,
        use_cerebellum=use_cerebellum,
        weights=None,
    )


def merge_synapse_blocks(blocks: List[SynapseBlock]) -> SynapseBlock:
    if not blocks:
        raise ValueError("Cannot merge empty list of blocks")

    reference_source = blocks[0].source_pop_label
    reference_target = blocks[0].target_pop_label

    for i, block in enumerate(blocks[1:], start=1):
        if (
            block.source_pop_label != reference_source
            or block.target_pop_label != reference_target
        ):
            raise ValueError(
                f"Inconsistent source_pop_label: block 0 has '{reference_source}>{reference_target}', "
                f"but block {i} has '{block.source_pop_label}>{block.target_pop_label}'"
            )

    return SynapseBlock(
        source_pop_label=blocks[0].source_pop_label,
        target_pop_label=blocks[0].target_pop_label,
        synapse_recordings=[r for b in blocks for r in b.synapse_recordings],
    )


def save_conn_weights(
    weights: list[SynapseBlock], dir: Path, filename_prefix: str, comm=None
) -> list[Path]:

    paths = []
    for block in weights:
        if comm is not None:
            # gather all blocks and merge them in a single object
            gathered: list[SynapseBlock] = comm.gather(block, root=0)
            if comm.rank == 0:
                block = merge_synapse_blocks(gathered)

        if comm is None or comm.rank == 0:
            label = f"{block.source_pop_label}>{block.target_pop_label}"
            rec_path = dir / f"{filename_prefix}-{label}.json"
            _log.debug(f"saving {label}, with {len(block.synapse_recordings)} synapses")
            with open(rec_path, "w") as f:
                json_array = block.model_dump_json(indent=2)
                f.write(json_array)
            paths.append(rec_path)
    return paths
