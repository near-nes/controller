import os
from pathlib import Path

import numpy as np
import structlog
from config.core_models import SimulationParams
from config.module_params import GLETrajGeneratorConfig, TrajGeneratorType

_log: structlog.stdlib.BoundLogger = structlog.get_logger("traj.generate_gle")


def generate_trajectory_gle(
    image_path: Path,
    sim: SimulationParams,
    gle_params: GLETrajGeneratorConfig,
) -> tuple[np.ndarray, int]:
    import torch
    from pfc_planner.src.config import PlannerParams
    from pfc_planner.src.factory import get_planner

    torch.set_num_threads(int(os.getenv("OMP_NUM_THREADS")))
    torch.manual_seed(sim.seed)
    # otherwise torch messes with OMP_NUM_THREADS;
    # then nest does `assert env(OMP_NUM_THREADS) == kernel.virtual_threads` and fails

    params = PlannerParams(
        model_type=TrajGeneratorType.GLE.value,
        resolution=sim.resolution,
        time_prep=sim.time_prep,
        time_move=sim.time_move,
        time_locked_with_feedback=sim.time_locked_with_feedback,
        time_grasp=sim.time_grasp,
        time_post=sim.time_post,
    )

    _log.debug(f"Getting GLE planner, expecting traj len {params.trajectory_length}")

    planner = get_planner(params, model_dir=gle_params.model_dir)

    _log.info(f"Loading image from {image_path}")
    predicted_trajectory, predicted_choice = planner.image_to_trajectory(image_path)
    predicted_choice_idx = 0 if predicted_choice == "left" else 1

    return predicted_trajectory, predicted_choice_idx
