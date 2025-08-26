import os
from dataclasses import dataclass
from pathlib import Path

COMPLETE_CONTROL = Path(__file__).parent.parent.resolve()
ROOT = COMPLETE_CONTROL.parent
RUNS_DIR = ROOT / "runs"  # Base directory for all runs

FOLDER_NAME_NEURAL_FIGS = "figs_neural"
FOLDER_NAME_ROBOTIC_FIGS = "figs_robotic"

REFERENCE_DATA_DIR = COMPLETE_CONTROL / "reference_data"

CONFIG = COMPLETE_CONTROL / "config"

TRAJECTORY = CONFIG / "trajectory.txt"
MOTOR_COMMANDS = CONFIG / "motor_commands.txt"
NESTML_BUILD_DIR = ROOT / "nestml" / "target"
CEREBELLUM = ROOT / "cerebellum"
CEREBELLUM_CONFIGS = ROOT / "cerebellum_configurations"
FORWARD = CEREBELLUM_CONFIGS / "forward.yaml"
INVERSE = CEREBELLUM_CONFIGS / "inverse.yaml"
BASE = CEREBELLUM_CONFIGS / "microzones_complete_nest.yaml"
PATH_HDF5 = os.environ.get("BSB_NETWORK_FILE")


@dataclass(frozen=True)
class RunPaths:
    """Holds the standard paths for a single simulation run."""

    run: Path
    data_nest: Path
    robot_result: Path
    figures: Path
    figures_receiver: Path
    logs: Path
    params_json: Path

    @classmethod
    def from_run_id(cls, run_timestamp: str):
        """
        Sets up the directory structure for a single simulation run.

        Args:
            run_timestamp: A string timestamp (e.g., YYYYMMDD_HHMMSS).

        Returns:
            RunPaths: A dataclass instance containing Path objects for
                                'run', 'data', 'figures', 'logs'.
        """
        run_dir = RUNS_DIR / run_timestamp
        data_dir = run_dir / "data"
        data_nest_dir = data_dir / "neural"
        robot_result = data_dir / "robotic" / "plant_data.json"
        figures_dir = run_dir / FOLDER_NAME_NEURAL_FIGS
        figures_receiver_dir = run_dir / FOLDER_NAME_ROBOTIC_FIGS
        logs_dir = run_dir / "logs"
        params_path = run_dir / f"params{run_timestamp}.json"

        # Create directories if they don't exist
        for dir_path in [
            run_dir,
            data_nest_dir,
            robot_result.parent,
            figures_dir,
            figures_receiver_dir,
            logs_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True, mode=0o770)

        return cls(
            run=run_dir,
            data_nest=data_nest_dir,
            robot_result=robot_result,
            figures=figures_dir,
            figures_receiver=figures_receiver_dir,
            logs=logs_dir,
            params_json=params_path,
        )


RUNS_DIR.mkdir(parents=True, exist_ok=True)
