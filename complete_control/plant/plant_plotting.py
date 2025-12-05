from datetime import datetime
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import structlog
import tqdm
from config.paths import RunPaths
from config.plant_config import PlantConfig
from config.ResultMeta import ResultMeta
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from utils_common.generate_signals import PlannerData
from utils_common.results import (
    extract_and_merge_plant_results,
    extract_time_move_trajectories,
)

from .plant_models import JointState, JointStates, PlantPlotData

(SHOULDER, ELBOW, HAND) = range(3)
log = structlog.get_logger(__name__)


def plot_ee_space(
    config: PlantConfig,
    desired_start_ee: np.ndarray,
    desired_end_ee: np.ndarray,
    actual_traj_ee: np.ndarray,  # Shape (num_time_steps, 3) for x,y,z
    save_fig: bool = True,
) -> None:
    """Plots end-effector space trajectory."""
    pth_fig_receiver = config.run_paths.figures_receiver
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    plot_init_marker_xz = [desired_start_ee[0], desired_start_ee[2]]
    plot_target_marker_xz = [desired_end_ee[0], desired_end_ee[2]]

    plt.figure()
    single_trial_steps = len(config.time_vector_single_trial_s)

    for trial_n in range(config.N_TRIALS):
        start_idx = trial_n * single_trial_steps
        end_idx = start_idx + single_trial_steps
        if end_idx > actual_traj_ee.shape[0]:
            end_idx = actual_traj_ee.shape[0]

        # Plot X (pos_ee_m_actual[:,0]) vs Z (pos_ee_m_actual[:,2])
        plt.plot(
            actual_traj_ee[start_idx:end_idx, 0],
            actual_traj_ee[start_idx:end_idx, 2],
            "k.",
            ms=1,
            label="Trajectory" if trial_n == 0 else None,
        )
        plt.plot(
            actual_traj_ee[end_idx - 1, 0],
            actual_traj_ee[end_idx - 1, 2],
            marker="x",
            color="k",
            label="Reached (End of Trial)" if trial_n == 0 else None,
        )

    plt.plot(
        plot_init_marker_xz[0],
        plot_init_marker_xz[1],
        marker="o",
        color="blue",
        label="Config Start EE",
    )
    plt.plot(
        plot_target_marker_xz[0],
        plot_target_marker_xz[1],
        marker="o",
        color="red",
        label="Config Target EE",
    )

    plt.axis("equal")
    plt.xlabel("Position X (m)")
    plt.ylabel("Position Z (m)")
    plt.title("End-Effector Trajectory")
    plt.legend()
    plt.tight_layout()
    if save_fig:
        filepath = pth_fig_receiver / f"position_ee_{timestamp}.png"
        plt.savefig(filepath)
        log.info(f"Saved end-effector space plot at {filepath}")
    plt.close()


def plot_motor_commands(
    pth_fig_receiver: Path,
    time_vector_s: np.ndarray,
    input_cmd_torque_actual: np.ndarray,
    save_fig: bool = True,
) -> None:
    """Plots motor commands (actual vs desired if available)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    MARKERSIZE = 0.8
    COLOR_ACTUAL = "m"
    LABEL_ACTUAL = "Actual Motor Command"

    fig, ax = plt.subplots()
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Motor Command (Torque N.m)")
    ax.set_title("Motor Commands")
    ax.set_xlim(time_vector_s.min(), time_vector_s.max())

    ax.plot(
        time_vector_s,
        input_cmd_torque_actual,
        markersize=MARKERSIZE,
        color=COLOR_ACTUAL,
        label=LABEL_ACTUAL,
    )
    ax.legend()
    fig.tight_layout()
    if save_fig:
        filepath = pth_fig_receiver / f"motCmd_{timestamp}.png"
        fig.savefig(filepath)
        log.info(f"Saved motor commands plot at {filepath}")
    plt.close()


def plot_errors_per_trial(
    config: PlantConfig,
    errors_list: List[float],  # List of final error per trial
    save_fig: bool = True,
) -> None:
    """Plots the final error for each trial."""
    if isinstance(errors_list[0], list):
        # for now, flatten. if we ever have error per joint, revisit
        errors_list = [leaf for tree in errors_list for leaf in tree]

    pth_fig_receiver = config.run_paths.figures_receiver
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cond_str = "refactored"

    plt.figure()
    plt.plot(range(1, len(errors_list) + 1), errors_list, marker="o")
    plt.xlabel("Trial Number")
    plt.ylabel("Final Error (rad or m, depending on error metric)")
    plt.title("Error per Trial")
    plt.grid(True)
    plt.tight_layout()
    if save_fig:
        filepath = pth_fig_receiver / f"{cond_str}_error_ee_trial_{timestamp}.png"
        plt.savefig(filepath)
        log.info(f"Saved error per trial plot at at {filepath}")
    plt.close()


def plot_joint_space_animated(
    pth_fig_receiver: Path,
    time_vector_s: np.ndarray,
    pos_j_rad_actual: np.ndarray,
    desired_trj_joint_rad: np.ndarray,
    animated: bool = True,
    video_duration: float = None,
    fps: float = 25,
    save_fig: bool = True,
) -> None:
    """Plots joint space position (actual vs desired)."""
    plt.rcParams.update({"font.size": 13})

    x = time_vector_s
    y1 = pos_j_rad_actual
    y2 = desired_trj_joint_rad
    filepath = None

    MARKERSIZE = 0.8
    COLOR_ACTUAL = "m"
    COLOR_DESIRED = "c"
    LABEL_ACTUAL = "Actual Joint Angle"
    LABEL_DESIRED = "Desired Joint Angle"

    fig, ax = plt.subplots()
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Joint Angle (rad)")
    ax.set_title("Joint Space Position")
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(y1.min() - 0.1, 2.8)

    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color=COLOR_ACTUAL,
            label=LABEL_ACTUAL,
            markersize=4,
            linestyle="None",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color=COLOR_DESIRED,
            label=LABEL_DESIRED,
            markersize=4,
            linestyle="None",
        ),
    ]
    ax.legend(handles=legend_elements, loc="lower left")
    fig.tight_layout()

    (line1,) = ax.plot(
        x if not animated else [],
        y1 if not animated else [],
        ".",
        markersize=MARKERSIZE,
        label=LABEL_ACTUAL,
        color=COLOR_ACTUAL,
    )
    (line2,) = ax.plot(
        x if not animated else [],
        y2 if not animated else [],
        ".",
        markersize=MARKERSIZE,
        label=LABEL_DESIRED,
        color=COLOR_DESIRED,
    )

    if animated:
        n_frames = video_duration * fps

        def update(frame):
            end = int(len(x) * frame / n_frames)
            line1.set_data(x[:end], y1[:end])
            line2.set_data(x[:end], y2[:end])
            return (line1, line2)

        ani = FuncAnimation(
            fig, update, frames=n_frames, interval=1000 / fps, blit=True
        )

    if save_fig:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if animated:
            with tqdm.tqdm(total=n_frames, unit="step", desc="Rendering") as pbar:
                filepath = pth_fig_receiver / f"anim_position_joint_{timestamp}.mp4"
                log.debug(f"Saving animated joint space plot at {filepath}...")
                ani.save(
                    filepath,
                    writer="ffmpeg",
                    fps=fps,
                    dpi=300,
                    progress_callback=lambda i, n: pbar.update(1),
                )
                log.info(f"Saved animated joint space plot at {filepath}")
        else:
            filepath = pth_fig_receiver / f"position_joint_{timestamp}.png"
            fig.savefig(filepath, dpi=300, transparent=False)
            log.info(f"Saved joint space plot at {filepath}")
    plt.close()
    return fig, ax, filepath


def plot_desired(
    config: PlantConfig,
    time_vector_s: np.ndarray,
    pos_j_rad_actual: np.ndarray,
    desired_trj_joint_rad: np.ndarray,
    save_fig: bool = True,
) -> None:
    """Plots joint space position (actual vs desired)."""
    pth_fig_receiver = config.run_paths.figures_receiver
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    COLOR_DESIRED = "c"
    plt.plot(
        time_vector_s,
        desired_trj_joint_rad,
        linestyle=":",
        linewidth=2,
        color=COLOR_DESIRED,
        label="Target Trajectory",
    )

    plt.xlabel("Time (s)")
    plt.ylabel("Joint Angle (rad)")
    plt.title("Joint Space Position")
    plt.legend()
    plt.ylim((0.0, 2.8))
    plt.tight_layout()
    if save_fig:
        filepath = pth_fig_receiver / f"desired_{timestamp}.png"
        plt.savefig(filepath, dpi=900)
        log.info(f"Saved joint space plot at {filepath}")
    plt.close()


def plot_rmse(
    metas: list[ResultMeta],
    pth_fig_receiver: Path,
    save_fig: bool = True,
) -> None:
    """Trials' RMSE plotting"""
    pos_j_actual, des_rad = extract_time_move_trajectories(metas)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = None

    elbow_rmse = [
        np.sqrt(np.mean(np.square(a - d))) for a, d in zip(pos_j_actual, des_rad)
    ]

    fig, ax = plt.subplots()
    ax.plot(np.arange(1, len(metas) + 1), elbow_rmse, "-o")
    ax.set_xlabel("Trial Number")
    ax.set_ylabel("Elbow RMSE (rad)")
    ax.set_title("Elbow RMSE Over Trials")
    fig.tight_layout()
    if save_fig:
        filepath = pth_fig_receiver / f"elbow_rmse_{timestamp}.png"
        fig.savefig(filepath)
        log.info(f"Saved joint RMSE plot at {filepath}")
    return fig, ax, filepath


def plot_plant_outputs(
    metas: list[ResultMeta],
    animated_task: bool = False,
    animated_plots: bool = False,
):
    """Loads all plant-related data and generates all plots."""
    log.info("Generating plant plots...")

    run_paths = [RunPaths.from_run_id(m.id) for m in metas]
    plant_data = extract_and_merge_plant_results(metas)
    params = [i.load_params() for i in metas]
    ref_mp = params[0]
    time_vector_total_s = np.arange(
        0,
        sum(p.simulation.duration_s for p in params),
        params[0].simulation.resolution / 1000,
    )
    ref_plant_config = PlantConfig(ref_mp)
    joint_data = plant_data.joint_data[ELBOW]
    trjs = []
    for rp in run_paths:
        with open(rp.trajectory, "r") as f:
            planner_data: PlannerData = PlannerData.model_validate_json(f.read())
            trjs.append(planner_data.trajectory)
    desired_trajectory = np.concatenate(trjs, axis=0)

    plot_rmse(metas, ref_plant_config.run_paths.figures_receiver)

    framerate = 25
    video_duration = 5
    if animated_task:
        generate_video_from_existing_result_single_trial(
            ref_plant_config,
            plant_data,
        )
        if (
            ref_mp.plotting.CAPTURE_VIDEO is None
            or len(ref_mp.plotting.CAPTURE_VIDEO) == 0
        ):
            log.warning(
                "Asked to generate task video but no frames were generated during run. Animated plots will use default time."
            )
        else:
            for ax in ref_mp.plotting.CAPTURE_VIDEO:
                video_duration = int(
                    len(ref_plant_config.time_vector_single_trial_s)
                    / ref_mp.plotting.NUM_STEPS_CAPTURE_VIDEO
                    / framerate
                )
                import ffmpeg

                ffmpeg.input(
                    f"{run_paths.video_frames / ax}/*.jpg",
                    pattern_type="glob",
                    framerate=framerate,
                    loglevel="warning",
                ).output(str((run_paths.figures / f"task_{ax}.mp4").absolute())).run()

    f, a, filepath = plot_joint_space_animated(
        pth_fig_receiver=ref_plant_config.run_paths.figures_receiver,
        time_vector_s=time_vector_total_s,
        pos_j_rad_actual=joint_data.pos_rad,
        desired_trj_joint_rad=desired_trajectory,
        animated=animated_plots,
        video_duration=video_duration,
        fps=framerate,
    )
    # plot_ee_space(
    #     config=ref_plant_config,
    #     desired_start_ee=np.array(plant_data.init_hand_pos_ee),
    #     desired_end_ee=np.array(plant_data.trgt_hand_pos_ee),
    #     actual_traj_ee=plant_data.ee_data.pos_ee,
    # )
    plot_motor_commands(
        pth_fig_receiver=ref_plant_config.run_paths.figures_receiver,
        time_vector_s=time_vector_total_s,
        input_cmd_torque_actual=joint_data.input_cmd_torque,
    )
    plot_errors_per_trial(config=ref_plant_config, errors_list=plant_data.error)

    # plot_desired(
    #     config=ref_plant_config,
    #     time_vector_s=ref_plant_config.time_vector_total_s,
    #     pos_j_rad_actual=joint_data.pos_rad,
    #     desired_trj_joint_rad=planner_data.trajectory,
    # )

    log.info("Plant plots generated.")


def generate_video_from_existing_result_single_trial(
    plant_config: PlantConfig,
    plant_data: PlantPlotData,
    framerate: int = 25,
    trial=0,
    AXES_TO_CAPTURE: list[str] = ["y"],
    complete_video_filename: str = "complete.mp4",
):
    """Creates animated video from AXES_TO_CAPTURE angles for a single trial

    Uses the series of JointStates recorded in plotting data to step through a
    single trial's worth of screenshots, every NUM_STEPS_CAPTURE_VIDEO. Has no
     reset capabilities, so it only generates a single trial (`trial`). Generated
     screenshots are included in `plant_config.run_paths.figures_receiver/{axis}`

    If multiple axes are provided, composite video is generated in
    `plant_config.run_paths.figures_receiver/{complete_video_filename}`
    """
    import ffmpeg
    import pybullet
    from plant.robotic_plant import RoboticPlant

    images_path = plant_config.run_paths.figures_receiver

    plant = RoboticPlant(plant_config, pybullet)
    data = plant_data.joint_data
    steps_single_trial = int(
        plant_config.master_config.simulation.duration_ms
        / plant_config.master_config.simulation.resolution
    )
    start = trial * steps_single_trial
    end = (trial + 1) * steps_single_trial
    steps = start - end
    len_max_frame_name = len(str(steps))
    [
        (images_path / axis).mkdir(parents=True, exist_ok=True)
        for axis in AXES_TO_CAPTURE
    ]
    for step in tqdm.tqdm(
        range(
            start,
            end,
            plant_config.master_config.plotting.NUM_STEPS_CAPTURE_VIDEO,
        ),
        desc="Frame generation:",
    ):
        state = JointStates(
            shoulder=JointState(data[0].pos_rad[step], data[0].vel_rad_s[step]),
            elbow=JointState(data[1].pos_rad[step], data[1].vel_rad_s[step]),
            hand=JointState(data[2].pos_rad[step], data[2].vel_rad_s[step]),
        )
        plant._set_pos_all_joints(state)

        for axis in AXES_TO_CAPTURE:
            image_path: Path = (
                images_path / axis / f"<{step:0{len_max_frame_name}d}>.jpg"
            )
            plant._capture_state_and_save(image_path, axis)
        if step > plant_config.master_config.simulation.neural_control_steps:
            plant.update_ball_position()

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
            framerate=framerate,
            loglevel="warning",
        ).output(str(video_path.absolute())).run()

    if len(AXES_TO_CAPTURE) > 1:
        with open(images_path / "inputs.txt", "w", encoding="utf-8") as f:
            for path in single_axis_videos:
                f.write(f"file '{path.absolute()}'\n")

        ffmpeg.input(
            images_path / "inputs.txt",
            format="concat",
            safe=0,
            loglevel="quiet",
        ).output(
            str((images_path / complete_video_filename).absolute()), c="copy"
        ).run()
