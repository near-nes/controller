import os

import numpy as np
import torch
from gle_planner import GLEPlanner
from PIL import Image
from torchvision import transforms


def generate_trajectory_gle(image_path: str, model_path: str) -> np.ndarray:
    """
    Generates a trajectory using the pre-trained GLEPlanner model.

    Args:
        image_path (str): Path to the input image for the planner.
        model_path (str): Path to the trained .pth model file.

    Returns:
        np.ndarray: The predicted trajectory as a NumPy array.
    """
    TRAJECTORY_LEN = 100  # Must match the trained model's configuration
    NUM_CHOICES = 2  # Must match the trained model's configuration

    # --- 1. Model Initialization ---
    gle_planner_model = GLEPlanner(
        tau=1.0, dt=0.01, num_choices=NUM_CHOICES, trajectory_length=TRAJECTORY_LEN
    )

    # --- 2. Load Trained Weights ---
    gle_planner_model.load_state_dict(torch.load(model_path))
    gle_planner_model.eval()

    # --- 3. Prepare Input Data ---
    image_transform = transforms.Compose(
        [
            transforms.Resize((100, 100)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            transforms.Lambda(lambda x: x.view(-1)),
        ]
    )

    input_image = Image.open(image_path).convert("RGB")
    input_tensor = image_transform(input_image)
    input_batch = input_tensor.unsqueeze(0)

    # --- 4. Get Model Prediction ---
    with torch.no_grad():
        # The forward pass runs the dynamics. Looping as in the evaluation script.
        for _ in range(20):
            model_output = gle_planner_model(input_batch)

    # --- 5. Process the Output ---
    predicted_trajectory_tensor = model_output[:, :TRAJECTORY_LEN]
    predicted_trajectory = predicted_trajectory_tensor.squeeze(0).cpu().numpy()

    return predicted_trajectory


if __name__ == "__main__":
    # Example usage:
    # This assumes the script is run from the root of the project, so paths are relative to that.
    # Adjust paths as necessary depending on your execution context.

    # It's better to make these paths absolute or relative to a known root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Make sure to adjust these paths if your file structure is different.
    img_path = os.path.join(project_root, "pfc-planner", "data", "flexion_5.bmp")
    mdl_path = os.path.join(
        project_root, "pfc-planner", "models", "trained_gle_planner.pth"
    )

    if not os.path.exists(img_path):
        print(f"Error: Image path not found at {img_path}")
    elif not os.path.exists(mdl_path):
        print(f"Error: Model path not found at {mdl_path}")
    else:
        print("Generating trajectory from GLE planner...")
        trajectory = generate_trajectory_gle(image_path=img_path, model_path=mdl_path)
        print("--- GLE Planner Output ---")
        print(f"Shape of Predicted Trajectory: {trajectory.shape}")
        print(f"First 5 points of Trajectory: {trajectory[:5]}")
