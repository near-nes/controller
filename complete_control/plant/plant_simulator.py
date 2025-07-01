from typing import Any, List, Tuple

import music
import structlog
from config.plant_config import PlantConfig
from utils_common.generate_analog_signals import generate_signals
from utils_common.log import tqdm

from . import plant_utils
from .plant_plotting import PlantPlotData
from .robotic_plant import RoboticPlant
from .sensoryneuron import SensoryNeuron


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
            run_paths: A RunPaths object with paths for the current run.
            pybullet_instance: The initialized PyBullet instance (e.g., p from `import pybullet as p`).
            connect_gui: Whether the RoboticPlant should connect to the PyBullet GUI.
        """
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger(
            type(self).__name__
        )
        self.log.info("Initializing PlantSimulator...")
        self.config: PlantConfig = config
        self.p = pybullet_instance
        self.music_setup = music_setup

        self.plant = RoboticPlant(config=self.config, pybullet_instance=self.p)
        self.log.debug("RoboticPlant initialized.")

        self._setup_music_communication()
        self._setup_sensory_system()
        self.log.debug("MUSIC communication and SensorySystem setup complete.")

        self.num_total_steps = len(self.config.time_vector_total_s)
        self.joint_data = [
            plant_utils.JointData.empty(self.num_total_steps)
            for _ in range(self.config.NJT)
        ]
        # For storing raw received spikes before processing (per joint)
        self.received_spikes_pos: List[List[Tuple[float, int]]] = [
            [] for _ in range(self.config.NJT)
        ]
        self.received_spikes_neg: List[List[Tuple[float, int]]] = [
            [] for _ in range(self.config.NJT)
        ]
        self.errors_per_trial: List[float] = []  # Store final error of each trial

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
            music.Index.GLOBAL,
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
            music.Index.GLOBAL,
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

    def _should_lock_joint(self, current_sim_time_s: float) -> bool:
        time_in_trial = current_sim_time_s % self.config.TIME_TRIAL_S
        # joint is locked in two situations:
        # 1. during TIME_POST: we keep the joint locked at his arrival place
        # 2. during TIME_PREP: state needs time to adapt to sensory
        return (
            self.config.TIME_PREP_S + self.config.TIME_MOVE_S
        ) < time_in_trial or time_in_trial < self.config.TIME_PREP_S

    def _set_joint_torque(self, joint_torque: float, current_sim_time_s: float) -> bool:
        if self._should_lock_joint(current_sim_time_s):
            self.plant.lock_joint()
            return
        self.plant.set_joint_torques([joint_torque])

    def _update_sensory_feedback(
        self, current_joint_pos_rad: float, current_sim_time_s: float
    ) -> None:
        """
        Updates all sensory neurons based on the current plant state.
        **Assumes NJT=1**
        """
        if self._should_mask_sensory_info(current_sim_time_s):
            current_joint_pos_rad = 0

        self.sensory_neurons_p[0].update(
            current_joint_pos_rad, self.config.RESOLUTION_S, current_sim_time_s
        )
        self.sensory_neurons_n[0].update(
            current_joint_pos_rad, self.config.RESOLUTION_S, current_sim_time_s
        )

    def run_simulation(self) -> None:
        """Runs the main simulation loop. **NJT==1**"""
        self.log.info(
            "Starting simulation loop...",
            total_duration_s=self.config.TOTAL_SIM_DURATION_S,
            resolution_s=self.config.RESOLUTION_S,
        )

        music_runtime = music.Runtime(self.music_setup, self.config.RESOLUTION_S)
        current_sim_time_s = 0.0
        step = 0

        with tqdm(total=self.num_total_steps, unit="step", desc="Simulating") as pbar:
            # Simulation loop
            # Loop while current_sim_time_s is less than the total duration.
            # Add a small epsilon to ensure the last step is processed if time is exact.
            # Simulation loop; TODO should this count in num_steps instead?
            while current_sim_time_s < self.config.TOTAL_SIM_DURATION_S - (
                self.config.RESOLUTION_S / 2.0
            ):
                # self.log.warning(f"starting receiver loop for step {step}...")
                current_sim_time_s = music_runtime.time()  # Current time from MUSIC

                if step >= self.num_total_steps:
                    self.log.warning(
                        "Step index exceeds data_array size, breaking loop.",
                        step=step,
                        max_steps=self.num_total_steps,
                        sim_time=current_sim_time_s,
                    )
                    break

                if not (step % 500):
                    self.log.debug(
                        "Simulation progress", step=step, sim_time_s=current_sim_time_s
                    )

                # 1. Get current plant state
                self.plant.update_stats()
                joint_pos_rad, joint_vel_rad_s = self.plant.get_joint_state()
                ee_pos_m, ee_vel_m_list = self.plant.get_ee_pose_and_velocity()

                # 2. Send sensory feedback via MUSIC
                self._update_sensory_feedback(joint_pos_rad, current_sim_time_s)

                # 3. Calculate motor command from received spikes
                # For NJT=1
                j = 0  # Current joint index
                buffer_start_time = current_sim_time_s - self.config.BUFFER_SIZE_S

                rate_pos_hz, _ = plant_utils.compute_spike_rate(
                    spikes=self.received_spikes_pos[j],
                    weight=self.config.WGT_MOTCTX_MOTNEUR,
                    n_neurons=self.config.N_NEURONS,
                    time_start=buffer_start_time,
                    time_end=current_sim_time_s,
                )
                rate_neg_hz, _ = plant_utils.compute_spike_rate(
                    spikes=self.received_spikes_neg[j],
                    weight=self.config.WGT_MOTCTX_MOTNEUR,
                    n_neurons=self.config.N_NEURONS,
                    time_start=buffer_start_time,
                    time_end=current_sim_time_s,
                )
                net_rate_hz = rate_pos_hz - rate_neg_hz
                computed_torque_from_input = net_rate_hz / self.config.SCALE_TORQUE

                # TODO: Add perturbation logic here if needed, to calculate input_cmd_total_torque

                # 4. Apply motor command to plant
                self._set_joint_torque(computed_torque_from_input, current_sim_time_s)

                # 5. Step PyBullet simulation
                self.plant.simulate_step(self.config.RESOLUTION_S)

                # 6. Record data for this step
                # For NJT=1
                self.joint_data[0].record_step(
                    step=step,
                    joint_pos_rad=joint_pos_rad,
                    joint_vel_rad_s=joint_vel_rad_s,
                    ee_pos_m=ee_pos_m,
                    ee_vel_m_s=ee_vel_m_list,
                    spk_rate_pos_hz=rate_pos_hz,
                    spk_rate_neg_hz=rate_neg_hz,
                    spk_rate_net_hz=net_rate_hz,
                    input_cmd_torque=computed_torque_from_input,
                )

                # 7. Trial end logic (reset plant)
                # Check if current_sim_time_s is at the end of a trial period
                # (timeMax + timeWait). Using fmod for float comparison robustness.
                # A trial ends right BEFORE the next one starts or at the very end of simulation.
                current_trial_time_s = current_sim_time_s % self.config.TIME_TRIAL_S
                # Check if we are close to the end of the active part of the trial (timeMax)
                # or more robustly, if we are at the end of the full trial period (timeMax + timeWait)
                # The original reset happened if tickt % time_trial == 0 (and not at t=0) OR at exp_duration - res

                # A trial is considered finished after (timeMax + timeWait)
                # So, reset happens when current_sim_time_s is a multiple of TIME_TRIAL_S
                # (but not at t=0, and also at the very end of the simulation)
                is_trial_end_time = False
                if step > 0:  # Avoid reset at the very beginning
                    # Check if current_sim_time_s is (almost) a multiple of TIME_TRIAL_S
                    # Or if it's the last step of the simulation
                    if abs(current_sim_time_s % self.config.TIME_TRIAL_S) < (
                        self.config.RESOLUTION_S / 2.0
                    ) or abs(
                        current_sim_time_s
                        - (self.config.TOTAL_SIM_DURATION_S - self.config.RESOLUTION_S)
                    ) < (
                        self.config.RESOLUTION_S / 2.0
                    ):
                        if not (
                            abs(current_sim_time_s) < self.config.RESOLUTION_S / 2.0
                            and step == 0
                        ):  # ensure not t=0
                            is_trial_end_time = True

                if is_trial_end_time:
                    final_error_rad = joint_pos_rad - self.config.target_joint_pos_rad
                    self.errors_per_trial.append(final_error_rad)
                    self.log.info(
                        "Trial finished. Resetting plant.",
                        trial_num=len(self.errors_per_trial),  # 1-based
                        sim_time_s=current_sim_time_s,
                        final_error_rad=final_error_rad,
                    )
                    self.plant.reset_plant()
                    # Clear spike buffers for the next trial? Original code did not explicitly clear spikes_pos/neg lists.
                    # MUSIC spikes are timestamped, so old spikes won't affect future rate calculations
                    # as long as the buffer_start_time correctly moves forward.

                # 8. Advance MUSIC time
                music_runtime.tick()
                step += 1
                # Update tqdm progress bar
                pbar.update(1)
                # pbar.set_postfix(sim_time_s=f"{current_sim_time_s:.2f}", refresh=True)
                # PyBullet is stepped by plant.simulate_step.
                # If direct p.stepSimulation() was used, it would be here.

        music_runtime.finalize()
        self.log.info("Simulation loop finished.")

        # After loop, finalize and save/plot
        self._finalize_and_process_data()

    def _finalize_and_process_data(self) -> None:
        """Saves all data required for post-simulation analysis and plotting."""
        self.log.info("Finalizing and saving simulation data...")

        sensory_spikes_p_all_joints: List[List[Tuple[float, int]]] = [
            sn.spike for sn in self.sensory_neurons_p
        ]
        sensory_spikes_n_all_joints: List[List[Tuple[float, int]]] = [
            sn.spike for sn in self.sensory_neurons_n
        ]

        plot_data = PlantPlotData(
            joint_data=self.joint_data,
            received_spikes={
                "pos": self.received_spikes_pos,
                "neg": self.received_spikes_neg,
            },
            sensory_spikes={
                "p": sensory_spikes_p_all_joints,
                "n": sensory_spikes_n_all_joints,
            },
            errors_per_trial=self.errors_per_trial,
            init_hand_pos_ee=list(self.plant.init_hand_pos_ee),
            trgt_hand_pos_ee=list(self.plant.trgt_hand_pos_ee),
        )
        plot_data.save(self.config.run_paths.robot_result)
        self.log.info(f"Saved plotting data to {self.config.run_paths.robot_result}")
