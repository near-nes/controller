import os
from dataclasses import dataclass
from pathlib import Path


def _get_root_path() -> Path:
    """
    Determine the ROOT path for the controller.

    Priority:
    1. CONTROLLER_DIR environment variable (for Docker/HPC compatibility)
    2. Parent directory of installed package (for pip install)
    3. Falls back to relative path based on current file location
    """
    # Check environment variable first (Docker/HPC usage)
    if "CONTROLLER_DIR" in os.environ:
        root = Path(os.environ["CONTROLLER_DIR"])
        if root.exists():
            return root

    # Fall back to package installation location
    # This file is at: <package>/complete_control/config/paths.py
    # We want to go up to: <package>/ which is the root
    this_file = Path(__file__).resolve()
    package_root = this_file.parent.parent.parent  # go up 3 levels to controller/

    if (package_root / "complete_control").exists():
        return package_root

    # Last resort: raise an error with helpful message
    raise RuntimeError(
        "Could not determine ROOT path. Either:\n"
        "1. Set CONTROLLER_DIR environment variable to the controller root directory\n"
        "2. Install this package properly with pip install\n"
        f"Expected package structure not found. Package root would be: {package_root}"
    )


ROOT = _get_root_path()
COMPLETE_CONTROL = ROOT / "complete_control"
RUNS_DIR = (
    Path(os.getenv("RUNS_PATH")) if os.getenv("RUNS_PATH") else (ROOT / "runs")
)  # Base directory for all runs

FOLDER_NAME_NEURAL_FIGS = "figs_neural"
FOLDER_NAME_ROBOTIC_FIGS = "figs_robotic"

REFERENCE_DATA_DIR = COMPLETE_CONTROL / "reference_data"

CONFIG = COMPLETE_CONTROL / "config"
ARTIFACTS = ROOT / "artifacts"
EMBODIMENT_ASSETS = ROOT / "embodiment_assets"

TRAJECTORY = CONFIG / "trajectory.txt"
MOTOR_COMMANDS = CONFIG / "motor_commands.txt"
NESTML_BUILD_DIR = ROOT / "nestml" / "target"
CEREBELLUM = ROOT.parent / "cerebellum"
CEREBELLUM_CONFIGS = ROOT / "cerebellum_configurations"
FORWARD = CEREBELLUM_CONFIGS / "forward.yaml"
INVERSE = CEREBELLUM_CONFIGS / "inverse.yaml"
BASE = CEREBELLUM_CONFIGS / "microzones_complete_nest.yaml"

# BSB network file path: check environment variable first, then fall back to artifacts
if "BSB_NETWORK_FILE" in os.environ:
    PATH_HDF5 = os.environ["BSB_NETWORK_FILE"]
else:
    # Fall back to decompressed file in artifacts
    _hdf5_path = ARTIFACTS / "cerebellum_plastic_base.hdf5"
    PATH_HDF5 = str(_hdf5_path) if _hdf5_path.exists() else None

SUBMODULES = ROOT / "submodules"

M1 = SUBMODULES / "motor_cortex_eprop"
MOTOR_MODEL = M1 / "motor_controller_model"
ARTIFACTS_M1 = ARTIFACTS / "m1"

PFC_PLANNER = SUBMODULES / "pfc_planner"
ARTIFACTS_PLANNER = ARTIFACTS / "pfc_planner"


@dataclass(frozen=True)
class RunPaths:
    """Holds the standard paths for a single simulation run."""

    run: Path
    input_image: Path
    data_nest: Path
    neural_result: Path
    robot_result: Path
    meta_result: Path
    figures: Path
    figures_receiver: Path
    logs: Path
    params_json: Path
    trajectory: Path
    video_frames: Path

    @classmethod
    def from_run_id(cls, run_timestamp: str, create_if_not_present=True):
        """
        Sets up the directory structure for a single simulation run.

        Args:
            run_timestamp: A string timestamp (e.g., YYYYMMDD_HHMMSS).

        Returns:
            RunPaths: A dataclass instance containing Path objects for
                                'run', 'data', 'figures', 'logs'.
        """
        id = run_timestamp.partition("-")[0]
        run_dir = RUNS_DIR / run_timestamp
        data_dir = run_dir / "data"
        data_nest_dir = data_dir / "neural"
        robot_result = data_dir / "robotic" / "plant_data.json"
        neural_result = run_dir / "neural_data.json"
        meta_result = run_dir / f"{id}.json"
        figures_dir = run_dir / FOLDER_NAME_NEURAL_FIGS
        figures_receiver_dir = run_dir / FOLDER_NAME_ROBOTIC_FIGS
        video_frames = run_dir / "video_frames"
        logs_dir = run_dir / "logs"
        params_path = run_dir / f"params{id}.json"
        input_image = run_dir / "input_image.bmp"
        trajectory = run_dir / "traj.npy"

        if create_if_not_present:
            for dir_path in [
                run_dir,
                data_nest_dir,
                robot_result.parent,
                figures_dir,
                figures_receiver_dir,
                video_frames,
                logs_dir,
            ]:
                dir_path.mkdir(parents=True, exist_ok=True, mode=0o775)

        return cls(
            run=run_dir,
            input_image=input_image,
            data_nest=data_nest_dir,
            neural_result=neural_result,
            meta_result=meta_result,
            robot_result=robot_result,
            figures=figures_dir,
            figures_receiver=figures_receiver_dir,
            video_frames=video_frames,
            logs=logs_dir,
            params_json=params_path,
            trajectory=trajectory,
        )


RUNS_DIR.mkdir(parents=True, exist_ok=True)
