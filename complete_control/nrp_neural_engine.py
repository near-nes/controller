"""NRP Neural Engine for the complete control simulation."""

import datetime

import structlog
from config.MasterParams import MasterParams
from config.paths import RunPaths
from neural.nest_adapter import initialize_nest, nest
from neural_simulation_lib import (
    create_controllers,
    setup_environment,
    setup_nest_kernel,
)
from nrp_core.engines.python_json import EngineScript
from utils_common.generate_analog_signals import generate_signals

NANO_SEC = 1e-9


class Script(EngineScript):
    def __init__(self):
        super().__init__()
        self.log = structlog.get_logger("nrp_neural_engine")
        initialize_nest("NRP")
        self.master_config = None
        self.controllers = []
        self.run_paths = None  # TOCHECK: How run_paths are handled in NRP context

    def initialize(self):
        self.log.info("NRP Neural Engine: Initializing...")
        print(nest.GetKernelStatus())

        run_timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        self.run_paths = RunPaths.from_run_id(run_timestamp_str)
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger("nrp_neural")
        self.log.info(f"Engine Log Path: {self.run_paths.logs}")

        self.master_config = MasterParams.from_runpaths(
            run_paths=self.run_paths, USE_MUSIC=False
        )
        self.log.info("MasterParams loaded successfully.")

        setup_environment()
        setup_nest_kernel(
            self.master_config.simulation,
            self.master_config.simulation.seed,
            self.run_paths.data_nest,
        )
        self.log.info("Environment and NEST kernel setup complete.")

        trj, motor_commands = generate_signals(
            self.master_config.experiment, self.master_config.simulation
        )
        self.log.info("Input data (trajectory, motor_commands) generated.")
        motor_commands = [float(i) for i in motor_commands]

        self.controllers = create_controllers(
            self.master_config,
            trj,
            motor_commands,
        )
        self.log.info(f"Created {len(self.controllers)} controllers.")

        self._registerDataPack("control_cmd")
        self._registerDataPack("positions")
        self._setDataPack("control_cmd", {"rate_pos": 0, "rate_neg": 0})
        self.log.info("Datapacks registered: control_cmd")

        nest.Prepare()
        self.log.info("NRP Neural Engine: Initialization complete.")

    def runLoop(self, timestep_ns):
        self.log.debug(
            f"NRP Neural Engine: runLoop at timestep {timestep_ns* NANO_SEC} sec"
        )

        # Read sensory data from input datapack
        feedback_data = self._getDataPack("positions")
        self.log.debug(f"Received feedback: {feedback_data}")

        self.controllers[0].update_sensory_info_from_NRP(feedback_data["joint_pos_rad"])
        nest.Run(timestep_ns * NANO_SEC)
        pos, neg = self.controllers[0].extract_motor_command_NRP(timestep_ns * NANO_SEC)

        self._setDataPack("control_cmd", {"rate_pos": pos, "rate_neg": neg})
        self.log.debug(f"Sent motor commands")

    def shutdown(self):
        self.log.info("NRP Neural Engine: Shutting down.")
        self.log.info("Data collapsing and plotting (if enabled) would occur here.")
        # from neural.data_handling import collapse_files
        # pop_views = []
        # for controller in self.controllers:
        #     pop_views.extend(controller.get_all_recorded_views())
        # collapse_files(self.run_paths.data_nest, pop_views) # TOCHECK: comm is not available
        # nest.Cleanup()

    # def reset(self):
    #     self.log.info("NRP Neural Engine: Resetting.")
    #     self.nest_client.Cleanup()

    #     if self.nest_client:
    #         self.nest_client.ResetKernel()

    #     self.initialize()
