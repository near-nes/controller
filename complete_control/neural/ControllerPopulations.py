from typing import Generic, Optional, TypeVar

from neural.neural_models import (
    RecordingManifest,
    convert_to_recording,
)
from pydantic import BaseModel

from .population_view import PopView

T = TypeVar("T")


class ControllerPopulationsGeneric(BaseModel, Generic[T]):
    """
    Holds the PopView instances for various populations in the controller.
    If CerebellumHandler is used, it will connect to the following populations from this dataclass:
    - mc_out_p, mc_out_n (Motor Cortex outputs)
    - planner_p, planner_n (Planner outputs)
    - sn_p, sn_n (Sensory inputs)
    - state_p, state_n (State Estimator outputs)
    - pred_p, pred_n (Prediction scaling neuron inputs, target for Fwd DCN)
    - brainstem_p, brainstem_n (Brainstem inputs, target for Inv DCN motor prediction)
    """

    # Planner
    planner_p: Optional[T] = None
    planner_n: Optional[T] = None
    # Motor Cortex
    mc_M1_p: Optional[T] = None
    mc_M1_n: Optional[T] = None
    mc_fbk_p: Optional[T] = None
    mc_fbk_n: Optional[T] = None
    mc_out_p: Optional[T] = None
    mc_out_n: Optional[T] = None
    # State Estimator
    state_p: Optional[T] = None
    state_n: Optional[T] = None
    # Sensory Input (Parrots)
    sn_p: Optional[T] = None
    sn_n: Optional[T] = None
    # Prediction Scaling (Diff Neurons)
    pred_p: Optional[T] = None
    pred_n: Optional[T] = None
    # Feedback Smoothing (Basic Neurons)
    fbk_smooth_p: Optional[T] = None
    fbk_smooth_n: Optional[T] = None
    # Brainstem Output (Basic Neurons)
    brainstem_p: Optional[T] = None
    brainstem_n: Optional[T] = None

    class Config:
        arbitrary_types_allowed = True


class ControllerPopulationsRecordings(ControllerPopulationsGeneric[RecordingManifest]):
    pass


class ControllerPopulations(ControllerPopulationsGeneric[PopView]):
    def to_recording(self, *args, **kwargs) -> ControllerPopulationsRecordings:
        return convert_to_recording(
            self, ControllerPopulationsRecordings, *args, **kwargs
        )
