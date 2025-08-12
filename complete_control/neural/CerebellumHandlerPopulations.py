from dataclasses import dataclass
from typing import List, Optional

from .population_view import PopView


@dataclass
class CerebellumHandlerPopulations:
    """
    Holds the PopView instances for interface populations created by CerebellumHandler.
    These populations mediate signals to/from the core cerebellum model or are
    involved in intermediate calculations within CerebellumHandler.
    """

    # === Inputs TO Core Cerebellum (via CerebellumHandler) ===
    # These are populations created by CerebellumHandler to scale/relay signals
    # before they reach the core cerebellum model (defined in cerebellum_build.py).

    # From Motor Cortex Output (scaled by basic_neuron_nestml, to Fwd Mossy Fibers)
    motor_commands: Optional[PopView] = None

    # From Planner (scaled by basic_neuron_nestml, to Inv Mossy Fibers)
    plan_to_inv: Optional[PopView] = None

    # From Sensory Neurons (scaled by basic_neuron_nestml, for Fwd Error Calculation input)
    feedback_p: Optional[PopView] = None
    feedback_n: Optional[PopView] = None

    # From Sensory Neurons (scaled by diff_neuron_nestml, for Inv Error Calculation input)
    # This is 'feedback_inv_p/n' in current cerebellum_controller.py
    feedback_inv_p: Optional[PopView] = None
    feedback_inv_n: Optional[PopView] = None

    # From State Estimator (scaled by basic_neuron_nestml, for Inv Error Calculation input)
    state_to_inv_p: Optional[PopView] = None
    state_to_inv_n: Optional[PopView] = None

    # === Error Calculation Populations (Input to Core Cerebellum IO) ===
    # These are diff_neuron_nestml populations created by CerebellumHandler.
    # Their inputs are other interface populations (e.g., feedback_p/n, DCN outputs).
    # Their outputs connect to the core cerebellum's IO cells.

    # Forward Model Error (calculated from feedback_p/n and Fwd DCN output; connects to Fwd IO)
    error_p: Optional[PopView] = None
    error_n: Optional[PopView] = None

    # Inverse Model Error (calculated from plan_to_inv_p/n and state_to_inv_p/n; connects to Inv IO)
    error_inv_p: Optional[PopView] = None
    error_inv_n: Optional[PopView] = None

    # === Outputs FROM Core Cerebellum (via CerebellumHandler) ===
    # These are populations created by CerebellumHandler to scale/relay signals
    # received from the core cerebellum model.

    # Inverse Model Motor Prediction (diff_neuron_nestml, scales output from Inv DCN)
    motor_prediction_p: Optional[PopView] = None
    motor_prediction_n: Optional[PopView] = None

    # Note: Forward model prediction (from Fwd DCN) is handled by CerebellumHandler
    # connecting core Fwd DCN PopViews (from CerebellumPopulations) directly
    # to 'pred_p'/'pred_n' populations within Controller.pops.
    # The 'prediction_p/n' fields that might have been in earlier versions of
    # CerebellumHandlerPopulations for this purpose are not needed here.

    def get_all_views(self) -> List[PopView]:
        """Helper to get all valid PopView objects stored in this dataclass."""
        views = []
        for pop_field_name in self.__dataclass_fields__:
            view = getattr(self, pop_field_name)
            if isinstance(view, PopView):
                views.append(view)
        return views
