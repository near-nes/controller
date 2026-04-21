"""Path resolution for the neurocontroller package.

Package-internal resources (YAML configs, reference data) are located via
``importlib.resources``, so they work regardless of install mode or CWD.
Runtime directories (RUNS_DIR, artifact dirs) fall back to ``$CWD`` when no
environment override is set.
"""

import os
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Optional

FOLDER_NAME_NEURAL_FIGS = "figs_neural"
FOLDER_NAME_ROBOTIC_FIGS = "figs_robotic"


# --- Package-internal resources --------------------------------------------

_PKG = files("neurocontroller")


def _pkg_path(*parts: str) -> Path:
    """Resolve a path inside the installed package as a concrete Path.

    Editable/flat installs always yield a real filesystem path; we cast to
    ``Path`` because the rest of the codebase and third-party libs (BSB,
    pybullet) expect string paths.
    """
    return Path(str(_PKG.joinpath(*parts)))


_CEREB_CONFIGS = _pkg_path("cerebellum_configurations")
FORWARD: Path = _CEREB_CONFIGS / "forward.yaml"
INVERSE: Path = _CEREB_CONFIGS / "inverse.yaml"
BASE: Path = _CEREB_CONFIGS / "microzones_complete_nest.yaml"

EMBODIMENT_ASSETS: Path = (
    Path(os.environ["EMBODIMENT_ASSETS_PATH"])
    if "EMBODIMENT_ASSETS_PATH" in os.environ
    else _pkg_path("embodiment_assets")
)


# --- Runtime directories ---------------------------------------------------


def _env_path(name: str) -> Optional[Path]:
    v = os.environ.get(name)
    return Path(v) if v else None


RUNS_DIR: Path = _env_path("RUNS_PATH") or (Path.cwd() / "runs")

# Optional: only used to capture the cerebellum repo's git hash in run metadata.
CEREBELLUM: Optional[Path] = _env_path("CEREBELLUM_PATH")


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
    def from_run_id(cls, run_timestamp: str, create_if_not_present: bool = True):
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
            RUNS_DIR.mkdir(parents=True, exist_ok=True, mode=0o775)
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
