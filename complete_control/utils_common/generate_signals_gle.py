import os
from pathlib import Path

import numpy as np
import structlog
from config.core_models import SimulationParams
from PIL import Image

_log: structlog.stdlib.BoundLogger = structlog.get_logger("traj.generate_gle")


def generate_trajectory_gle(
    image_path: Path, model_path: Path, sim: SimulationParams
) -> np.ndarray:

    import torch
    from pfc_planner.src.gle_conv_planner import GLEConvPlanner
    from torchvision import transforms

    torch.set_num_threads(int(os.getenv("OMP_NUM_THREADS")))
    # otherwise torch messes with OMP_NUM_THREADS;
    # then nest does `assert env(OMP_NUM_THREADS) == kernel.virtual_threads` and fails

    """
    Generates a trajectory using the pre-trained GLEPlanner model.

    Args:
        image_path (str): Path to the input image for the planner.
        model_path (str): Path to the trained .pth model file.

    Returns:
        np.ndarray: The predicted trajectory as a NumPy array.
    """
    TRAJECTORY_LEN = sim.neural_control_steps
    NUM_CHOICES = 2

    # --- Model Initialization ---
    _log.debug(
        f"Attempting to load GLEConvPlanner, expecting traj len to be {TRAJECTORY_LEN}"
    )
    gle_planner_model = GLEConvPlanner(
        tau=1.0, dt=0.1, num_choices=NUM_CHOICES, trajectory_length=TRAJECTORY_LEN
    )

    try:
        gle_planner_model.load_state_dict(torch.load(model_path))
    except RuntimeError as e:
        _log.error(
            f"Model was trained using diffferent sizes from provided one ({TRAJECTORY_LEN})"
        )
        raise e
    gle_planner_model.eval()

    # --- Prepare Input Data ---
    image_transform = transforms.Compose(
        [
            transforms.Resize((100, 100)),
            transforms.ToTensor(),
        ]
    )

    _log.info(f"loading image from {image_path}")
    input_image = Image.open(image_path).convert("RGB")
    input_tensor = image_transform(input_image)
    input_batch = input_tensor.unsqueeze(0)

    # --- Get Model Prediction ---
    with torch.no_grad():
        # The forward pass runs the dynamics. Looping as in the evaluation script.
        for _ in range(20):
            model_output = gle_planner_model(input_batch)

    # --- Process the Output ---
    predicted_trajectory_tensor, pred_choice_logits = (
        model_output[:, :TRAJECTORY_LEN],
        model_output[:, TRAJECTORY_LEN:],
    )
    predicted_trajectory = predicted_trajectory_tensor.squeeze(0).cpu().numpy()
    _, predicted_choice_idx = torch.max(pred_choice_logits, 1)

    predicted_trajectory_padded = np.concatenate(
        [predicted_trajectory, np.zeros(sim.manual_control_steps)]
    )

    return predicted_trajectory_padded, predicted_choice_idx
