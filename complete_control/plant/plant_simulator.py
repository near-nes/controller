from typing import List, Tuple

import numpy as np
import structlog
from config.core_models import TargetColor
from config.plant_config import PlantConfig
from utils_common.utils import TrialSection, get_current_section

from .plant_models import EEData, JointData, PlantPlotData
from .robotic_plant import RoboticPlant


class PlantSimulator:
    """
    Main orchestrator for the robotic plant simulation.
    Initializes and manages simulation components,
    runs simulation steps, and coordinates data recording and plotting.
    """

    def __init__(
        self,
        config: PlantConfig,
        pybullet_instance,
    ):
        """
        Initializes the PlantSimulator.

        Args:
            config: a PlantConfig object.
            pybullet_instance: The initialized PyBullet instance (e.g., p from `import pybullet as p`).
        """
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger(
            type(self).__name__
        )
        self.log.info("Initializing PlantSimulator...")
        self.config: PlantConfig = config
        self.p = pybullet_instance

        self.plant = RoboticPlant(config=self.config, pybullet_instance=self.p)
        self.log.debug("RoboticPlant initialized.")

        self.num_total_steps = len(self.config.time_vector_total_s)
        total_num_joints = (
            self.config.master_config.NJT + self.config.master_config.JOINTS_NO_CONTROL
        )
        self.joint_data = [
            JointData.empty(self.num_total_steps) for _ in range(total_num_joints)
        ]
        self.ee_data: EEData = EEData.empty(self.num_total_steps)
        # For storing raw received spikes before processing (per joint)
        self.received_spikes_pos: List[List[Tuple[float, int]]] = [
            [] for _ in range(self.config.NJT)
        ]
        self.received_spikes_neg: List[List[Tuple[float, int]]] = [
            [] for _ in range(self.config.NJT)
        ]
        self.plant._capture_state_and_save(self.config.run_paths.input_image)
        self.checked_proximity = False
        self.shoulder_moving = False

        for ax in self.config.master_config.plotting.CAPTURE_VIDEO:
            (self.config.run_paths.video_frames / ax).mkdir(exist_ok=True, parents=True)

        # TODO this has to be saved from planner, and currently it's not. mock it!
        if (
            self.config.master_config.simulation.oracle.target_color
            == TargetColor.BLUE_LEFT
        ):
            self.direction = 0.1
        else:
            self.direction = -0.1

        self.max_len_frame_name = len(
            str(self.config.TOTAL_SIM_DURATION_S * 1000 * self.config.RESOLUTION_MS)
        )

        self.log.info("PlantSimulator initialization complete.")

    def _grasp_if_target_close(self) -> float:
        if not self.checked_proximity:
            self.log.debug(
                "In TIME_GRASP. Verifying whether EE is in range for attachment..."
            )
            self.checked_proximity = True
            if self.plant.check_target_proximity():
                self.log.debug("EE is in range. Attaching...")
                self.target_attached = True
                self.plant.grasp()
            else:
                self.target_attached = False
                self.log.debug("EE is not in range. not attaching.")
        return 1 if self.target_attached else 0  # torque

    def _move_shoulder(self, direction) -> float:
        if self.target_attached and not self.shoulder_moving:
            self.log.debug("Moving shoulder...")
            self.plant.move_shoulder(direction)
            self.shoulder_moving = True
            return 1
        if self.target_attached:
            self.plant.update_ball_position()
            return 1
        return 0

    def run_simulation_step(
        self,
        rate_pos_hz: float,
        rate_neg_hz: float,
        current_sim_time_s: float,
        step: int,
    ) -> Tuple[float, float, List[float], List[float]]:
        """Execute one simulation step.

        Returns:
            Tuple containing (joint_pos_rad, joint_vel_rad_s, ee_pos_m, ee_vel_m_list)
            where ee_pos_m and ee_vel_m_list are lists representing end effector
            position and velocity
        """
        joint_states = self.plant.get_joint_states()
        joint_pos_rad, joint_vel_rad_s = joint_states.elbow
        ee_pos_m, ee_vel_m_list = self.plant.get_ee_pose_and_velocity()
        curr_section = get_current_section(
            current_sim_time_s * 1000, self.config.master_config
        )

        if step >= self.num_total_steps:
            self.log.warning(
                "Step index exceeds data_array size, breaking loop.",
                step=step,
                max_steps=self.num_total_steps,
                sim_time=current_sim_time_s,
            )
            return joint_pos_rad, joint_vel_rad_s, ee_pos_m, ee_vel_m_list, curr_section

        net_rate_hz = rate_pos_hz - rate_neg_hz
        elbow_torque = net_rate_hz / self.config.SCALE_TORQUE
        hand_torque = shoulder_torque = 0

        if self.config.master_config.plotting.CAPTURE_VIDEO and not (
            step % self.config.master_config.plotting.NUM_STEPS_CAPTURE_VIDEO
        ):
            for ax in self.config.master_config.plotting.CAPTURE_VIDEO:
                self.plant._capture_state_and_save(
                    self.config.run_paths.video_frames
                    / ax
                    / f"{step:0{self.max_len_frame_name}d}.jpg",
                    axis=ax,
                )

        if not (step % 500):
            self.log.debug(
                "Simulation progress", step=step, sim_time_s=current_sim_time_s
            )

        self.plant.update_stats()

        if curr_section == TrialSection.TIME_MOVE:
            self.plant.set_elbow_joint_torque([elbow_torque])
        else:
            self.plant.lock_elbow_joint()

        if curr_section == TrialSection.TIME_GRASP:
            hand_torque = self._grasp_if_target_close()

        if curr_section == TrialSection.TIME_POST:
            shoulder_torque = self._move_shoulder(self.direction)

        # Step PyBullet simulation
        self.plant.simulate_step(self.config.RESOLUTION_S)

        imposed_torques = [hand_torque, elbow_torque, shoulder_torque]
        for torque, (i, state) in zip(
            imposed_torques,
            enumerate(joint_states),
        ):
            self.joint_data[i].record_step(step, state.pos, state.vel, torque)

        self.ee_data.record_step(step, ee_pos_m, ee_vel_m_list)

        return joint_pos_rad, joint_vel_rad_s, ee_pos_m, ee_vel_m_list, curr_section

    def finalize_and_process_data(self, reached_joint_rad) -> PlantPlotData:
        """Saves all data required for post-simulation analysis and plotting."""
        self.log.info("Finalizing and saving simulation data...")
        error = reached_joint_rad - self.config.target_joint_pos_rad

        plot_data = PlantPlotData(
            joint_data=self.joint_data,
            ee_data=self.ee_data,
            error=[error],
            init_hand_pos_ee=list(self.plant.init_hand_pos_ee),
            trgt_hand_pos_ee=list(self.plant.trgt_hand_pos_ee),
        )
        tmp_filename = self.config.run_paths.robot_result.with_suffix(".tmp")
        final_filename = self.config.run_paths.robot_result
        plot_data.save(tmp_filename)
        # save + rename to have atomic write
        tmp_filename.rename(final_filename)
        return plot_data
