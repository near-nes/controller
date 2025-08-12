from typing import List

from pydantic import BaseModel

from complete_control.utils_common.custom_types import NdArray


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
