from dataclasses import dataclass
from pathlib import Path
from typing import List

from neural.population_view import PopView
from pydantic import BaseModel
from utils_common.custom_types import NdArray


class ConvertToRecording:
    # Class variable that subclasses should override
    RecordingClass = None

    def convert_to_recording(self):
        if self.RecordingClass is None:
            raise NotImplementedError("RecordingClass must be set in subclass")

        dest = self.RecordingClass()
        for k, v in self.__dict__.items():
            if isinstance(v, PopView):
                setattr(dest, k, v.collect())
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
