import datetime
import os
import sys
from pathlib import Path

import numpy as np
import pybullet
import structlog

sys.path.insert(0, "/sim/controller/complete_control")
os.environ["RUNS_PATH"] = str((Path(__file__).parent / "runs").absolute())

import ffmpeg
from tqdm import tqdm

from complete_control.config.core_models import (
    OracleData,
    SimulationParams,
    TargetColor,
)
from complete_control.config.paths import RunPaths
from complete_control.config.plant_config import PlantConfig
from complete_control.plant.robotic_plant import RoboticPlant

AXES_TO_CAPTURE = [
    # "x",
    "y",
    # "z",
]
FRAC_MOVE = 0.6
FRAC_GRASP = 0
FRAC_SHOULDER = 1 - FRAC_MOVE - FRAC_GRASP
DURATION = 5  # seconds
FRAMERATE = 25
COLOR = TargetColor.RED_RIGHT
START_ANGLE_ELBOW = 20
FINAL_ANGLE_ELBOW = 140
START_ANGLE_SHOULDER = 0
FINAL_ANGLE_SHOULDER = 0
TARGET_ANGLE = 140
SPEED_GRASP = 1
PYBULLET_STEP = 0.5

exec_key = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
TOTAL_FRAMES = DURATION * FRAMERATE
FRAME_MOVE = int(TOTAL_FRAMES * FRAC_MOVE)
FRAME_GRASP = int(TOTAL_FRAMES * FRAC_GRASP)
FRAME_SHOULDER = 1 + int(TOTAL_FRAMES * FRAC_SHOULDER)
ANGLE_INCREMENT_ELBOW = np.deg2rad((START_ANGLE_ELBOW - FINAL_ANGLE_ELBOW) / FRAME_MOVE)
ANGLE_INCREMENT_SHOULDER = np.deg2rad(
    (START_ANGLE_SHOULDER - FINAL_ANGLE_SHOULDER) / FRAME_SHOULDER
)
GRASP_OCCURS = False
# TARGET_ANGLE == FINAL_ANGLE_ELBOW


if __name__ == "__main__":
    log = structlog.get_logger("")

    images_path = (
        Path(".")
        / f"{exec_key}-{COLOR.name}-{DURATION}s-{'grasp' if GRASP_OCCURS else 'fail'}"
    )
    for axis in AXES_TO_CAPTURE:
        (images_path / axis).mkdir(exist_ok=True, parents=True)
    run_paths = RunPaths.from_run_id(exec_key)
    config = PlantConfig.from_runpaths(
        run_paths,
        simulation=SimulationParams(
            oracle=OracleData(
                init_joint_angle=START_ANGLE_ELBOW,
                tgt_joint_angle=TARGET_ANGLE,
                target_color=COLOR,
            )
        ),
    )
    plant = RoboticPlant(config, pybullet)

    current_angle_elbow = np.deg2rad(START_ANGLE_ELBOW)

    current_angle_shoulder = np.deg2rad(START_ANGLE_SHOULDER)
    len_max_frame_name = len(str(TOTAL_FRAMES))
    log.debug(
        f"starting frame gen with start={START_ANGLE_ELBOW}deg, curr={current_angle_elbow}, incr={ANGLE_INCREMENT_ELBOW}, targ={FINAL_ANGLE_ELBOW}deg"
    )
    log.debug(f"{FRAME_MOVE}+{FRAME_GRASP}+{FRAME_SHOULDER}≃{TOTAL_FRAMES}")
    prep_shoulder = False
    with tqdm(total=TOTAL_FRAMES, unit="frame", desc="Rendering") as pbar:
        for frame in range(TOTAL_FRAMES):
            frame_lexicographic = f"{frame:0{len_max_frame_name}d}"
            if frame < FRAME_MOVE:
                plant._set_rad_elbow(current_angle_elbow)
                current_angle_elbow -= ANGLE_INCREMENT_ELBOW
            elif not GRASP_OCCURS:
                pass
            elif frame < (FRAME_MOVE + FRAME_GRASP):
                if not prep_shoulder:
                    plant.move_shoulder(0)
                    prep_shoulder = True
                plant.simulate_step(PYBULLET_STEP)
            else:
                plant._set_rad_shoulder(current_angle_shoulder)
                plant.update_ball_position()
                current_angle_shoulder -= ANGLE_INCREMENT_SHOULDER

            for axis in AXES_TO_CAPTURE:
                image_path = (
                    images_path
                    / axis
                    / f"<{frame_lexicographic}>{START_ANGLE_ELBOW}-{int(np.rad2deg(current_angle_elbow))}-{TARGET_ANGLE}.jpg"
                )
                plant._capture_state_and_save(image_path, axis)
            pbar.update(1)
    plant.p.resetSimulation()
    plant.p.disconnect()

    single_axis_videos = []
    for axis in AXES_TO_CAPTURE:
        axis_path = images_path / axis
        video_path = axis_path / "task.mp4"
        single_axis_videos.append(video_path)
        ffmpeg.input(
            f"{axis_path}/*.jpg",
            pattern_type="glob",
            framerate=FRAMERATE,
            # loglevel="quiet",
        ).output(str(video_path.absolute())).run()

    if len(AXES_TO_CAPTURE) > 1:
        with open(images_path / "inputs.txt", "w", encoding="utf-8") as f:
            for path in single_axis_videos:
                f.write(f"file '{path.absolute()}'\n")

        ffmpeg.input(
            images_path / "inputs.txt",
            format="concat",
            safe=0,
        ).output(str((images_path / "complete.mp4").absolute()), c="copy").run()
