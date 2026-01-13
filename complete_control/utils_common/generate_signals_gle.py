import os
from pathlib import Path

import numpy as np
import structlog
from config.core_models import SimulationParams

_log: structlog.stdlib.BoundLogger = structlog.get_logger("traj.generate_gle")


def generate_trajectory_gle(
    image_path: Path, model_path: Path, sim: SimulationParams
) -> np.ndarray:

    import torch
    from pfc_planner.src.config import PlannerParams
    from pfc_planner.src.planners import GLEPlanner, GLEPlannerNet

    torch.set_num_threads(int(os.getenv("OMP_NUM_THREADS")))
    # otherwise torch messes with OMP_NUM_THREADS;
    # then nest does `assert env(OMP_NUM_THREADS) == kernel.virtual_threads` and fails

    """
    Generates a trajectory using the pre-trained GLEPlanner model.

    Args:
        image_path (Path): Path to the input image for the planner.
        model_path (Path): Path to the trained .pth model file.

    Returns:
        np.ndarray: The predicted trajectory as a NumPy array.
    """
    planner_params = PlannerParams(
        model_type="gle",
        num_choices=2,
        image_size=(100, 100),
        gle_tau=1.0,
        gle_beta=1.0,
        resolution=sim.resolution,
        time_prep=sim.time_prep,
        time_move=sim.time_move,
        time_grasp=sim.time_grasp,
        time_post=sim.time_post,
    )

    _log.debug(
        f"Attempting to load GLEPlanner, expecting traj len to be {planner_params.trajectory_length}"
    )

    net = GLEPlannerNet(params=planner_params)
    gle_planner_model = GLEPlanner(params=planner_params, net=net)
    gle_planner_model.load_model(model_path)

    _log.info(f"loading image from {image_path}")
    predicted_trajectory, predicted_choice = gle_planner_model.image_to_trajectory(
        image_path
    )
    predicted_choice_idx = 0 if predicted_choice == "left" else 1

    return predicted_trajectory, predicted_choice_idx
