from dataclasses import dataclass
from pathlib import Path
from typing import List

from neural.population_view import PopView
from pydantic import BaseModel
from utils_common.custom_types import NdArray

T = TypeVar("T")


def convert_to_recording(
    source: object, target_class: type[T], path: Path, comm=None
) -> T:
    from neural.population_view import PopView

    """Convert a population object to its recording equivalent."""
    dest = target_class()
    for k, v in source.__dict__.items():
        if isinstance(v, PopView):
            setattr(dest, k, v.collect(path, comm))
    return dest


@dataclass
class PopulationBlocks:
    controller: ConvertToRecording = None
    cerebellum_handler: ConvertToRecording = None
    cerebellum: ConvertToRecording = None


class RecordingManifest(BaseModel):
    population_spikes: Path


class PopulationSpikes(BaseModel):
    """
    Represents the spiking data and metadata for a single neuron population.
    """

    label: str
    gids: NdArray
    senders: NdArray
    times: NdArray
    population_size: int
    neuron_model: str

    class Config:
        arbitrary_types_allowed = True


class SynapseRecording(BaseModel):
    weight_history: List[float]
    source: int  # GID
    target: int  # GID
    syn_type: str
    syn_id: int

    class Config:
        arbitrary_types_allowed = True


class SynapseBlock(BaseModel):
    source_pop_label: str
    target_pop_label: str
    synapse_recordings: List[SynapseRecording]
