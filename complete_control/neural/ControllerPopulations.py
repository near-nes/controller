# controller.py (Add this at the top or in a separate types.py)
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

# Assuming PopView is imported from population_view.py
from .population_view import PopView


@dataclass
class ControllerPopulations:
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
    planner_p: Optional[PopView] = None
    planner_n: Optional[PopView] = None
    # Motor Cortex
    mc_ffwd_p: Optional[PopView] = None
    mc_ffwd_n: Optional[PopView] = None
    mc_fbk_p: Optional[PopView] = None
    mc_fbk_n: Optional[PopView] = None
    mc_out_p: Optional[PopView] = None
    mc_out_n: Optional[PopView] = None
    # State Estimator
    state_p: Optional[PopView] = None
    state_n: Optional[PopView] = None
    # Sensory Input (Parrots)
    sn_p: Optional[PopView] = None
    sn_n: Optional[PopView] = None
    # Prediction Scaling (Diff Neurons)
    pred_p: Optional[PopView] = None
    pred_n: Optional[PopView] = None
    # Feedback Smoothing (Basic Neurons)
    fbk_smooth_p: Optional[PopView] = None
    fbk_smooth_n: Optional[PopView] = None
    # Brainstem Output (Basic Neurons)
    brainstem_p: Optional[PopView] = None
    brainstem_n: Optional[PopView] = None
    # Add any other populations if needed

    # Helper to get all valid PopView objects (useful for iteration)
    def get_all_views(self) -> List[PopView]:
        views = []
        for pop_field in self.__dataclass_fields__:
            view = getattr(self, pop_field)
            if isinstance(view, PopView):
                views.append(view)
        return views

    # Helper to get underlying NEST nodes for all views
    def get_all_nest_nodes(self) -> List[Any]:
        nodes = []
        for view in self.get_all_views():
            if view.pop:  # Check if pop exists
                nodes.extend(view.pop)  # Assumes view.pop is iterable (NodeCollection)
        return nodes
