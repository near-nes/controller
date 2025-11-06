from typing import Generic, Optional, TypeVar

from neural.neural_models import (
    RecordingManifest,
    convert_to_recording,
)
from pydantic import BaseModel

from .population_view import PopView

T = TypeVar("T")


class CerebellumHandlerPopulationsGeneric(BaseModel, Generic[T]):
    """
    Holds the PopView instances for interface populations created by CerebellumHandler.
    These populations mediate signals to/from the core cerebellum model or are
    involved in intermediate calculations within CerebellumHandler.
    """

    # === Inputs TO Core Cerebellum ===
    # From Motor Cortex Output (scaled by basic_neuron_nestml, to Fwd Mossy Fibers)
    motor_commands: Optional[T] = None

    # From Planner (scaled by basic_neuron_nestml, to Inv Mossy Fibers)
    plan_to_inv: Optional[T] = None

    # From Sensory Neurons (scaled by basic_neuron_nestml, for Fwd Error Calculation input)
    feedback_p: Optional[T] = None
    feedback_n: Optional[T] = None

    # From Sensory Neurons (scaled by diff_neuron_nestml, for Inv Error Calculation input)
    feedback_inv_p: Optional[T] = None
    feedback_inv_n: Optional[T] = None

    # From State Estimator (scaled by basic_neuron_nestml, for Inv Error Calculation input)
    state_to_inv_p: Optional[T] = None
    state_to_inv_n: Optional[T] = None

    # === Error Calculation Populations (Input to Core Cerebellum IO) ===
    # Forward Model Error (calculated from feedback_p/n and Fwd DCN output; connects to Fwd IO)
    error_p: Optional[T] = None
    error_n: Optional[T] = None

    # Inverse Model Error (calculated from plan_to_inv_p/n and state_to_inv_p/n; connects to Inv IO)
    error_inv_p: Optional[T] = None
    error_inv_n: Optional[T] = None

    # === Outputs FROM Core Cerebellum (via CerebellumHandler) ===
    # Inverse Model Motor Prediction (diff_neuron_nestml, scales output from Inv DCN)
    motor_prediction_p: Optional[T] = None
    motor_prediction_n: Optional[T] = None

    class Config:
        arbitrary_types_allowed = True


class CerebellumHandlerPopulationsRecordings(
    CerebellumHandlerPopulationsGeneric[RecordingManifest]
):
    pass


class CerebellumHandlerPopulations(CerebellumHandlerPopulationsGeneric[PopView]):
    def to_recording(self, *args, **kwargs) -> CerebellumHandlerPopulationsRecordings:
        return convert_to_recording(
            self, CerebellumHandlerPopulationsRecordings, *args, **kwargs
        )
