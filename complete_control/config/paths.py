import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.getenv("CONTROLLER_DIR"))
COMPLETE_CONTROL = ROOT / "complete_control"
RUNS_DIR = Path(os.getenv("RUNS_PATH", ROOT / "runs"))  # Base directory for all runs

FOLDER_NAME_NEURAL_FIGS = "figs_neural"
FOLDER_NAME_ROBOTIC_FIGS = "figs_robotic"

REFERENCE_DATA_DIR = COMPLETE_CONTROL / "reference_data"

CONFIG = COMPLETE_CONTROL / "config"
ARTIFACTS = ROOT / "artifacts"

TRAJECTORY = CONFIG / "trajectory.txt"
MOTOR_COMMANDS = CONFIG / "motor_commands.txt"
NESTML_BUILD_DIR = ROOT / "nestml" / "target"
CEREBELLUM = ROOT.parent / "cerebellum"
CEREBELLUM_CONFIGS = ROOT / "cerebellum_configurations"
FORWARD = CEREBELLUM_CONFIGS / "forward.yaml"
INVERSE = CEREBELLUM_CONFIGS / "inverse.yaml"
BASE = CEREBELLUM_CONFIGS / "microzones_complete_nest.yaml"
PATH_HDF5 = os.environ.get("BSB_NETWORK_FILE")

SUBMODULES = ROOT / "submodules"

M1 = SUBMODULES / "motor_cortex" / "eprop-motor-control"
M1_CONFIG = M1 / "config" / "config.yaml"
M1_WEIGHTS = (
    M1 / "sim_results" / "default_plastic_False_manualRBF_False" / "trained_weights.npz"
)

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
                dir_path.mkdir(parents=True, exist_ok=True, mode=0o770)

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
