from datetime import datetime
from pathlib import Path
from typing import ClassVar, List

import matplotlib.pyplot as plt
import numpy as np
import structlog
import tqdm
from config.MasterParams import MasterParams
from config.paths import RunPaths
from config.plant_config import PlantConfig
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from pydantic import BaseModel

from complete_control.utils_common.draw_schema import draw_schema
from complete_control.utils_common.generate_signals import PlannerData

from .plant_models import JointState, JointStates, PlantPlotData

(SHOULDER, ELBOW, HAND) = range(3)
log = structlog.get_logger(__name__)


def plot_joint_space(
    config: PlantConfig,
    time_vector_s: np.ndarray,
    pos_j_rad_actual: np.ndarray,
    desired_trj_joint_rad: np.ndarray,
    save_fig: bool = True,
) -> None:
    """Plots joint space position (actual vs desired)."""
    pth_fig_receiver = config.run_paths.figures_receiver
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    plt.figure()
    plt.plot(
        time_vector_s, pos_j_rad_actual[:], linewidth=2, label="Actual Joint Angle"
    )

    # Construct full desired trajectory for plotting
    # The config.trajectory_joint_single_trial_rad is for one trial.
    # We need to tile it or use a pre-computed full desired trajectory.
    # For now, let's plot only actual if full desired isn't readily available.
    # Or, plot the single trial desired trajectory overlaid repeatedly.

    # Example: Overlaying the single trial desired trajectory for each trial period
    single_trial_steps = len(config.time_vector_single_trial_s)
    desired_single_trial = desired_trj_joint_rad

    full_desired_plot = np.full_like(pos_j_rad_actual[:], np.nan)
    for trial_n in range(config.N_TRIALS):
        start_idx = trial_n * single_trial_steps
        end_idx = start_idx + len(desired_single_trial)
        if end_idx <= len(full_desired_plot):
            full_desired_plot[start_idx:end_idx] = desired_single_trial
        else:  # partial last trial
            len_to_copy = len(full_desired_plot) - start_idx
            if len_to_copy > 0:
                full_desired_plot[start_idx:] = desired_single_trial[:len_to_copy]

    plt.plot(
        time_vector_s,
        full_desired_plot,
        linestyle=":",
        linewidth=2,
        label="Desired Joint Angle (Per Trial)",
    )

    plt.xlabel("Time (s)")
    plt.ylabel("Joint Angle (rad)")
    plt.title("Joint Space Position")
    plt.legend()
    plt.ylim((0.0, 2.8))
    plt.tight_layout()
    if save_fig:
        filepath = pth_fig_receiver / f"position_joint_{timestamp}.png"
        plt.savefig(filepath)
        log.info(f"Saved joint space plot at {filepath}")
    plt.close()


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
    config: PlantConfig,
    time_vector_s: np.ndarray,
    input_cmd_torque_actual: np.ndarray,
    # input_cmd_torque_desired: np.ndarray, # If available
    save_fig: bool = True,
) -> None:
    """Plots motor commands (actual vs desired if available)."""
    pth_fig_receiver = config.run_paths.figures_receiver
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cond_str = "refactored"  # Placeholder for condition string from original plots

    plt.figure()
    plt.plot(time_vector_s, input_cmd_torque_actual[:], label="Actual Motor Command")
    # if input_cmd_torque_desired is not None:
    #     plt.plot(time_vector_s, input_cmd_torque_desired[:,0], linestyle=':', label="Desired Motor Command")
    plt.xlabel("Time (s)")
    plt.ylabel("Motor Command (Torque N.m)")  # Assuming torque
    plt.title("Motor Commands")
    plt.legend()
    plt.tight_layout()
    if save_fig:
        filepath = pth_fig_receiver / f"{cond_str}_motCmd_{timestamp}.png"
        plt.savefig(filepath)
        log.info(f"Saved motor commands plot at {filepath}")
    plt.close()


def plot_errors_per_trial(
    config: PlantConfig,
    errors_list: List[float],  # List of final error per trial
    save_fig: bool = True,
) -> None:
    """Plots the final error for each trial."""
    if not errors_list:
        log.info("No errors to plot.")
        return

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
    config: PlantConfig,
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
    pth_fig_receiver = config.run_paths.figures_receiver

    x = time_vector_s
    y1 = pos_j_rad_actual
    y2 = desired_trj_joint_rad

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
            fig.savefig(filepath, dpi=900, transparent=False)
            log.info(f"Saved joint space plot at {filepath}")
    plt.close()


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


def plot_plant_outputs(
    run_paths: RunPaths,
    animated_task: bool = False,
    animated_plots: bool = False,
):
    """Loads all plant-related data and generates all plots."""
    log.info("Generating plant plots...")

    with open(run_paths.params_json, "r") as f:
        master_params = MasterParams.model_validate_json(f.read())
    config = PlantConfig(master_params)
    config.run_paths = run_paths
    plant_data = PlantPlotData.load(run_paths.robot_result)

    if not plant_data.joint_data:
        log.error("No joint data found.")
        return

    joint_data = plant_data.joint_data[ELBOW]
    with open(run_paths.trajectory, "r") as f:
        planner_data: PlannerData = PlannerData.model_validate_json(f.read())

    generate_video_from_existing_result_single_trial(
        config,
        plant_data,
    )
    plot_joint_space_animated(
        config=config,
        time_vector_s=config.time_vector_total_s,
        pos_j_rad_actual=joint_data.pos_rad,
        desired_trj_joint_rad=planner_data.trajectory,
        animated=animated_plots,
        video_duration=video_duration,
        fps=framerate,
    )
    plot_ee_space(
        config=config,
        desired_start_ee=np.array(plant_data.init_hand_pos_ee),
        desired_end_ee=np.array(plant_data.trgt_hand_pos_ee),
        actual_traj_ee=plant_data.ee_data.pos_ee,
    )
    plot_motor_commands(
        config=config,
        time_vector_s=config.time_vector_total_s,
        input_cmd_torque_actual=joint_data.input_cmd_torque,
    )
    if plant_data.errors_per_trial:
        plot_errors_per_trial(config=config, errors_list=plant_data.errors_per_trial)

    plot_desired(
        config=config,
        time_vector_s=config.time_vector_total_s,
        pos_j_rad_actual=joint_data.pos_rad,
        desired_trj_joint_rad=planner_data.trajectory,
    )
    draw_schema(run_paths, scale_factor=0.005)

    log.info("Plant plots generated.")
