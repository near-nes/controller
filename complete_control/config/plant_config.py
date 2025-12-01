import numpy as np
import structlog

from . import paths
from .core_models import MetaInfo, SimulationParams
from .MasterParams import MasterParams


class PlantConfig:
    """
    Manages all configuration parameters for the robotic plant simulation.
    """

    def __init__(
        self,
        master_params: MasterParams,
    ):
        self.log = structlog.get_logger(type(self).__name__)
        self.log.info("Initializing PlantConfig...")
        self.master_config = master_params

        self.run_paths: paths.RunPaths = master_params.run_paths
        self.trajectory_path = paths.TRAJECTORY

        self.SEED = SimulationParams.get_default_seed()
        np.random.seed(self.SEED)

        # Simulation timing from MasterConfig
        self.RESOLUTION_MS: float = self.master_config.simulation.resolution
        self.RESOLUTION_S: float = self.RESOLUTION_MS / 1000.0
        self.TIME_MOVE_MS: float = self.master_config.simulation.time_move
        self.TIME_MOVE_S: float = self.TIME_MOVE_MS / 1000.0
        self.TIME_PREP_MS: float = self.master_config.simulation.time_prep
        self.TIME_PREP_S: float = self.TIME_PREP_MS / 1000.0
        self.TIME_GRASP_MS: int = self.master_config.simulation.time_grasp
        self.TIME_GRASP_S: int = self.master_config.simulation.time_grasp / 1000.0
        self.TIME_POST_MS: float = self.master_config.simulation.time_post
        self.TIME_POST_S: float = self.TIME_POST_MS / 1000.0

        self.TIME_TRIAL_S: float = self.master_config.simulation.duration_ms / 1000.0
        self.TOTAL_SIM_DURATION_S: float = (
            self.master_config.simulation.duration_ms / 1000.0
        )

        self.time_vector_total_s: np.ndarray = np.arange(
            0, self.TOTAL_SIM_DURATION_S, self.RESOLUTION_S
        )
        self.time_vector_single_trial_s: np.ndarray = np.arange(
            0, self.TIME_TRIAL_S, self.RESOLUTION_S
        )

        self.NJT = self.master_config.NJT
        self.CONNECT_GUI = self.master_config.GUI_PYBULLET

        self.initial_joint_pos_rad: float = (
            self.master_config.simulation.oracle.init_pos_angle_rad
        )
        self.target_joint_pos_rad: float = (
            self.master_config.simulation.oracle.tgt_pos_angle_rad
        )

        self.N_NEURONS: int = self.master_config.brain.population_size

        # Plant interaction parameters (remain as is for Stage 1)
        self.SCALE_TORQUE: float = 5000.0  # 500000.0
        self.BUFFER_SIZE_S: float = 1.0 / 100.0

        # MUSIC configuration from MasterConfig
        self.MUSIC_CONST_S: float = (
            self.master_config.music.const / 1000.0
        )  # Assuming const in MusicConfigModel is in ms
        self.MUSIC_ACCEPTABLE_LATENCY_S: float = 2 * self.RESOLUTION_S - (
            self.RESOLUTION_S - self.MUSIC_CONST_S
        )
        if self.MUSIC_ACCEPTABLE_LATENCY_S < 0:
            self.MUSIC_ACCEPTABLE_LATENCY_S = 0.0
        self.MUSIC_PORT_MOT_CMD_IN: str = self.master_config.music.port_motcmd_in
        self.MUSIC_PORT_FBK_OUT: str = self.master_config.music.port_fbk_out

        # Sensory Neuron parameters from MasterConfig
        self.SENS_NEURON_BASE_RATE: float = (
            self.master_config.modules.spine.sensNeur_base_rate
        )
        self.SENS_NEURON_KP: float = self.master_config.modules.spine.sensNeur_kp
        self.SENS_NEURON_ID_START: int = self.master_config.brain.first_id_sens_neurons

        # Weight for motor command calculation from MasterConfig
        self.WGT_MOTCTX_MOTNEUR: float = (
            self.master_config.modules.spine.wgt_motCtx_motNeur
        )

        self.PLOT_DATA_FILENAME = "plant_plot_data.json"

        self.log.info("PlantConfig initialized successfully from MasterConfig")

    @classmethod
    def from_runpaths(
        cls,
        run_paths: paths.RunPaths,
        **kwargs,
    ):
        return cls(MasterParams.from_runpaths(run_paths, **kwargs))
