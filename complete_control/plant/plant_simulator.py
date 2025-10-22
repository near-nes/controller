import time
from enum import Enum
from typing import Any, List, Tuple

import numpy as np
import structlog
from config.plant_config import PlantConfig
from utils_common.log import tqdm

from complete_control.config.core_models import TargetColor

from . import plant_utils
from .plant_models import EEData, JointData, PlantPlotData
from .robotic_plant import RoboticPlant
from .sensoryneuron import SensoryNeuron


class TrialSection(Enum):
    TIME_START, TIME_PREP, TIME_MOVE, TIME_GRASP, TIME_POST, TIME_END_TRIAL = range(6)


class PlantSimulator:
    """
    Main orchestrator for the robotic plant simulation.
    Initializes and manages simulation components, handles MUSIC communication,
    runs the simulation loop, and coordinates data recording and plotting.
    """

    def __init__(
        self,
        config: PlantConfig,
        pybullet_instance,
        music_setup,
    ):
        """
        Initializes the PlantSimulator.

        Args:
            config: a PlantConfig object.
            pybullet_instance: The initialized PyBullet instance (e.g., p from `import pybullet as p`).
            music_setup: when None, assume Music is not being used (i.e. NRP).
        """
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger(
            type(self).__name__
        )
        self.log.info("Initializing PlantSimulator...")
        self.config: PlantConfig = config
        self.p = pybullet_instance
        self.music_enabled = music_setup is not None

        self.plant = RoboticPlant(config=self.config, pybullet_instance=self.p)
        self.log.debug("RoboticPlant initialized.")

        if self.music_enabled:
            import music

            self.music = music
            self.music_setup = music_setup
            self._setup_music_communication()
            self._setup_sensory_system()

            self.log.debug("MUSIC communication and SensorySystem setup complete.")

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
        self.errors_per_trial: List[float] = []  # Store final error of each trial
        self.plant._capture_state_and_save(self.config.run_paths.input_image)
        self.checked_proximity = False
        self.shoulder_moving = False

        # TODO this has to be saved from planner, and currently it's not. mock it!
        if (
            self.config.master_config.simulation.oracle.target_color
            == TargetColor.BLUE_LEFT
        ):
            self.direction = 0.1
        else:
            self.direction = -0.1

        self.log.info("PlantSimulator initialization complete.")

    def _setup_music_communication(self) -> None:
        """Sets up MUSIC input and output ports and handlers."""
        self.log.debug("Setting up MUSIC communication...")
        self.music_input_port = self.music_setup.publishEventInput(
            self.config.MUSIC_PORT_MOT_CMD_IN
        )
        self.music_output_port = self.music_setup.publishEventOutput(
            self.config.MUSIC_PORT_FBK_OUT
        )

        # Configure input port mapping
        # nlocal: total number of neurons this MUSIC instance expects to handle inputs for.
        # In original: N * 2 * njt (N positive, N negative, for each joint)
        n_music_channels_in = self.config.N_NEURONS * 2 * self.config.NJT
        self.music_input_port.map(
            self._music_inhandler,
            self.music.Index.GLOBAL,
            base=0,
            size=n_music_channels_in,
            accLatency=self.config.MUSIC_ACCEPTABLE_LATENCY_S,
        )
        self.log.info(
            "MUSIC input port configured",
            port_name=self.config.MUSIC_PORT_MOT_CMD_IN,
            channels=n_music_channels_in,
            acc_latency=self.config.MUSIC_ACCEPTABLE_LATENCY_S,
        )

        # Configure output port mapping
        # Sensory neurons will connect to this port. Mapping is global, base 0, size N*2*njt.
        n_music_channels_out = self.config.N_NEURONS * 2 * self.config.NJT
        self.music_output_port.map(
            self.music.Index.GLOBAL,
            base=self.config.SENS_NEURON_ID_START,  # Global ID start for these sensory neurons
            size=n_music_channels_out,
        )
        self.log.info(
            "MUSIC output port configured",
            port_name=self.config.MUSIC_PORT_FBK_OUT,
            base_id=self.config.SENS_NEURON_ID_START,
            channels=n_music_channels_out,
        )

    def _music_inhandler(self, t: float, indextype: Any, channel_id: int) -> None:
        """
        MUSIC input handler called for each received spike.
        Populates received_spikes_pos and received_spikes_neg.
        """
        # Determine which joint and population (pos/neg) the spike belongs to.
        # Original logic:
        # var_id = int(channel_id / (N * 2))  (joint_id)
        # tmp_id = channel_id % (N * 2)
        # flagSign = tmp_id / N  (<1 for pos, >=1 for neg)

        # Assuming channel_id is global and needs to be mapped if base is not 0 in sender.
        # However, the map call uses base=0, size=n_music_channels_in, so channel_id is 0 to n_music_channels_in-1.

        joint_id = int(channel_id / (self.config.N_NEURONS * 2))

        if not (0 <= joint_id < self.config.NJT):
            self.log.error(
                "Received spike for invalid joint_id",
                channel_id=channel_id,
                derived_joint_id=joint_id,
                max_njt=self.config.NJT - 1,
            )
            return

        local_channel_in_joint_block = channel_id % (self.config.N_NEURONS * 2)

        # Relative spike time to simulation start could be `t - initial_offset_if_any`
        # but MUSIC `t` should be global simulation time.
        spike_time = t

        if local_channel_in_joint_block < self.config.N_NEURONS:  # Positive population
            self.received_spikes_pos[joint_id].append((spike_time, channel_id))
        else:  # Negative population
            self.received_spikes_neg[joint_id].append((spike_time, channel_id))

    def _setup_sensory_system(self) -> None:
        """Creates and configures SensoryNeuron instances."""
        self.log.debug("Setting up SensorySystem...")
        self.sensory_neurons_p: List[SensoryNeuron] = []
        self.sensory_neurons_n: List[SensoryNeuron] = []

        for j in range(self.config.NJT):
            # Positive sensory neurons for joint j
            id_start_p = self.config.SENS_NEURON_ID_START + (
                2 * self.config.N_NEURONS * j
            )
            sn_p = SensoryNeuron(
                self.config.N_NEURONS,
                pos=True,
                idStart=id_start_p,
                bas_rate=self.config.SENS_NEURON_BASE_RATE,
                kp=self.config.SENS_NEURON_KP,
                res=self.config.RESOLUTION_S,
                music_index_strategy=self.music.Index.GLOBAL,
            )
            sn_p.connect(self.music_output_port)
            self.sensory_neurons_p.append(sn_p)

            # Negative sensory neurons for joint j
            id_start_n = id_start_p + self.config.N_NEURONS
            sn_n = SensoryNeuron(
                self.config.N_NEURONS,
                pos=False,
                idStart=id_start_n,
                bas_rate=self.config.SENS_NEURON_BASE_RATE,
                kp=self.config.SENS_NEURON_KP,
                res=self.config.RESOLUTION_S,
                music_index_strategy=self.music.Index.GLOBAL,
            )
            sn_n.connect(self.music_output_port)
            self.sensory_neurons_n.append(sn_n)

        self.log.info(
            "Sensory neurons created and connected",
            num_joints=self.config.NJT,
            neurons_per_pop=self.config.N_NEURONS,
        )

    def _should_mask_sensory_info(self, current_sim_time_s: float) -> bool:
        "mask sensory during TIME_BEFORE_NEXT"
        time_in_trial = current_sim_time_s % self.config.TIME_TRIAL_S
        return (self.config.TIME_PREP_S + self.config.TIME_MOVE_S) < time_in_trial

    def music_end_step(
        self, joint_pos_rad: float, current_sim_time_s: float, music_runtime
    ) -> None:
        if self._should_mask_sensory_info(current_sim_time_s):
            joint_pos_rad = 0.0

        self.sensory_neurons_p[0].update(joint_pos_rad, current_sim_time_s)
        self.sensory_neurons_n[0].update(joint_pos_rad, current_sim_time_s)
        music_runtime.tick()

    def music_prepare_step(
        self, current_sim_time_s: float
    ) -> Tuple[float, float, float, float]:
        # Calculate buffer window for spike rate computation
        buffer_start_time = current_sim_time_s - self.config.BUFFER_SIZE_S

        # For NJT=1, we only process joint 0
        j = 0

        rate_pos_hz, _ = plant_utils.compute_spike_rate(
            spikes=self.received_spikes_pos[j],
            n_neurons=self.config.N_NEURONS,
            time_start=buffer_start_time,
            time_end=current_sim_time_s,
        )
        rate_neg_hz, _ = plant_utils.compute_spike_rate(
            spikes=self.received_spikes_neg[j],
            n_neurons=self.config.N_NEURONS,
            time_start=buffer_start_time,
            time_end=current_sim_time_s,
        )

        return rate_pos_hz, rate_neg_hz

    def _grasp_if_target_close(self):
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

    def _move_shoulder(self, direction):
        if self.target_attached and not self.shoulder_moving:
            self.log.debug("Moving shoulder...")
            self.plant.move_shoulder(direction)
            self.shoulder_moving = True
        if self.target_attached:
            self.plant.update_ball_position()

    def get_current_section(self, curr_time_s: float):
        if curr_time_s == 0:
            return TrialSection.TIME_START
        elif 0 <= (curr_time_s % self.config.TIME_TRIAL_S) < self.config.RESOLUTION_S:
            return TrialSection.TIME_END_TRIAL
        time_in_trial = curr_time_s % self.config.TIME_TRIAL_S
        if time_in_trial <= self.config.TIME_PREP_S:
            return TrialSection.TIME_PREP
        elif time_in_trial <= (self.config.TIME_MOVE_S + self.config.TIME_PREP_S):
            return TrialSection.TIME_MOVE
        elif time_in_trial <= (
            self.config.TIME_MOVE_S + self.config.TIME_PREP_S + self.config.TIME_GRASP_S
        ):
            return TrialSection.TIME_GRASP
        else:
            return TrialSection.TIME_POST

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
        curr_section = self.get_current_section(current_sim_time_s)

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

        if not (step % 500):
            self.log.debug(
                "Simulation progress", step=step, sim_time_s=current_sim_time_s
            )

        self.plant.update_stats()
        # Enable perturbation/gravity
        self._check_gravity(current_sim_time_s)

        if curr_section == TrialSection.TIME_MOVE:
            self.plant.set_elbow_joint_torque([elbow_torque])
        else:
            self.plant.lock_elbow_joint()

        if curr_section == TrialSection.TIME_GRASP:
            self._grasp_if_target_close()

        if curr_section == TrialSection.TIME_POST:
            self._move_shoulder(self.direction)

        # Step PyBullet simulation
        self.plant.simulate_step(self.config.RESOLUTION_S)

        imposed_torques = [elbow_torque, None, None]
        for torque, (i, state) in zip(
            imposed_torques,
            enumerate(joint_states),
        ):
            self.joint_data[i].record_step(step, state.pos, state.vel, torque)

        self.ee_data.record_step(step, ee_pos_m, ee_vel_m_list)

        # Trial end logic (reset plant if needed)
        if curr_section == TrialSection.TIME_END_TRIAL:
            final_error_rad = joint_pos_rad - self.config.target_joint_pos_rad
            self.errors_per_trial.append(final_error_rad)
            self.log.info(
                "Trial finished. Resetting plant.",
                trial_num=len(self.errors_per_trial),
                sim_time_s=current_sim_time_s,
                final_error_rad=final_error_rad,
            )
            self.checked_proximity = False
            self.target_attached = False
            self.plant.reset_plant()
            self.plant.reset_target()

        return joint_pos_rad, joint_vel_rad_s, ee_pos_m, ee_vel_m_list, curr_section

    def _check_gravity(self, current_sim_time_s: float):
        """Check trial number and enable/disable gravity"""
        exp_params = self.config.master_config.experiment

        if exp_params.enable_gravity:
            current_trial = int(current_sim_time_s / self.config.TIME_TRIAL_S)

            if current_trial >= exp_params.gravity_trial_start:
                self.plant.set_gravity(True, exp_params.z_gravity_magnitude)
            if (
                exp_params.gravity_trial_end is not None
                and current_trial > exp_params.gravity_trial_end
            ):
                self.plant.set_gravity(False)

    def run_simulation(self) -> None:
        """Runs the main simulation loop. **NJT==1**"""
        self.log.info(
            "Starting simulation loop...",
            total_duration_s=self.config.TOTAL_SIM_DURATION_S,
            resolution_s=self.config.RESOLUTION_S,
        )

        music_runtime = self.music.Runtime(self.music_setup, self.config.RESOLUTION_S)
        current_sim_time_s = 0.0
        step = 0

        with tqdm(total=self.num_total_steps, unit="step", desc="Simulating") as pbar:
            while current_sim_time_s < self.config.TOTAL_SIM_DURATION_S - (
                self.config.RESOLUTION_S / 2.0
            ):
                # Get commands from MUSIC
                rate_pos, rate_neg = self.music_prepare_step(current_sim_time_s)

                # Run simulation step
                joint_pos, joint_vel, ee_pos, ee_vel, curr_section = (
                    self.run_simulation_step(
                        rate_pos, rate_neg, current_sim_time_s, step
                    )
                )

                # Send sensory feedback through MUSIC
                self.music_end_step(joint_pos, current_sim_time_s, music_runtime)

                # Update progress
                current_sim_time_s += self.config.RESOLUTION_S
                step += 1
                pbar.update(1)

        music_runtime.finalize()
        self.log.info("Simulation loop finished.")

        # After loop, finalize and save/plot
        self._finalize_and_process_data()

    def _finalize_and_process_data(self) -> None:
        """Saves all data required for post-simulation analysis and plotting."""
        self.log.info("Finalizing and saving simulation data...")

        plot_data = PlantPlotData(
            joint_data=self.joint_data,
            ee_data=self.ee_data,
            errors_per_trial=self.errors_per_trial,
            init_hand_pos_ee=list(self.plant.init_hand_pos_ee),
            trgt_hand_pos_ee=list(self.plant.trgt_hand_pos_ee),
        )
        plot_data.save(self.config.run_paths.robot_result)
        self.log.info(f"Saved plotting data to {self.config.run_paths.robot_result}")
