from datetime import datetime
from pathlib import Path
from typing import ClassVar, List

import matplotlib.pyplot as plt
import numpy as np
import structlog
from config.MasterParams import MasterParams
from config.paths import RunPaths
from config.plant_config import PlantConfig
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


def plot_plant_outputs(run_paths: RunPaths):
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

    # Generate plots
    plot_joint_space(
        config=config,
        time_vector_s=config.time_vector_total_s,
        pos_j_rad_actual=joint_data.pos_rad,
        desired_trj_joint_rad=planner_data.trajectory,
    )
    plot_ee_space(
        config=config,
        desired_start_ee=np.array(plant_data.init_hand_pos_ee),
        desired_end_ee=np.array(plant_data.trgt_hand_pos_ee),
        actual_traj_ee=joint_data.pos_ee_m,
    )
    plot_motor_commands(
        config=config,
        time_vector_s=config.time_vector_total_s,
        input_cmd_torque_actual=joint_data.input_cmd_torque,
    )
    if plant_data.errors_per_trial:
        plot_errors_per_trial(config=config, errors_list=plant_data.errors_per_trial)

    draw_schema(run_paths, scale_factor=0.005)

    log.info("Plant plots generated.")
