"""NRP Neural Engine for the complete control simulation."""

import os

import structlog
from config.MasterParams import MasterParams
from config.paths import COMPLETE_CONTROL, RunPaths
from neural.nest_adapter import initialize_nest, nest
from neural.plot_utils import plot_controller_outputs
from neural_simulation_lib import (
    create_controllers,
    setup_environment,
    setup_nest_kernel,
)
from nrp_core.engines.python_json import EngineScript
from utils_common.generate_analog_signals import generate_signals
from utils_common.profile import Profile

NANO_SEC = 1e-9


class Script(EngineScript):
    def __init__(self):
        super().__init__()
        self.log = structlog.get_logger("nrp_neural_engine")
        initialize_nest("NRP")
        self.master_config = None
        self.controllers = []
        self.step = 0
        self.run_paths = None  # TOCHECK: How run_paths are handled in NRP context

    def initialize(self):
        self.log.info("NRP Neural Engine: Initializing...")
        self.log.debug(nest.GetKernelStatus())
        self.step = 0

        run_timestamp_str = os.getenv("EXEC_TIMESTAMP")

        self.run_paths = RunPaths.from_run_id(run_timestamp_str)
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger("nrp_neural")
        self.log.info(f"Engine Log Path: {self.run_paths.logs}")

        self.master_config = MasterParams.from_runpaths(self.run_paths, USE_MUSIC=False)
        with open(self.run_paths.params_json, "w") as f:
            f.write(self.master_config.model_dump_json(indent=2))
        self.log.info("MasterParams loaded and dumped successfully.")

        setup_environment()
        setup_nest_kernel(
            self.master_config.simulation,
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
        self.sensory_profile = Profile()
        self.sim_profile = Profile()
        self.motor_profile = Profile()
        self.rest_profile = Profile()

        self._registerDataPack("control_cmd")
        self._registerDataPack("positions")
        self._setDataPack("control_cmd", {"rate_pos": 0, "rate_neg": 0})
        self.log.info("Datapacks registered: control_cmd")

        nest.Prepare()
        self.log.info("NRP Neural Engine: Initialization complete.")

    def runLoop(self, timestep_ns):
        self.rest_profile.end()
        if self.step % 50 == 0:
            self.log.debug("[neural] starting neural update...")

        feedback_data = self._getDataPack("positions")
        joint_pos_rad = feedback_data["joint_pos_rad"]
        sim_time_s = self._time_ns * NANO_SEC

        with self.sensory_profile.time():
            self.controllers[0].update_sensory_info_from_NRP(
                joint_pos_rad, sim_time_s * 1000
            )

        if self.step % 50 == 0:
            self.log.debug("[neural] updated sensory info")

        with self.sim_profile.time():
            nest.Run(timestep_ns * NANO_SEC * 1000)

        if self.step % 50 == 0:
            self.log.debug("[neural] simulated")

        with self.motor_profile.time():
            pos, neg = self.controllers[0].extract_motor_command_NRP()

        if self.step % 50 == 0:
            self.log.debug(
                f"[neural] Update {self.step} complete.",
                sim_time=sim_time_s,
                rate_pos=int(pos),
                rate_neg=int(neg),
                angle=joint_pos_rad,
                time_sensory=str(self.sensory_profile.total_time),
                time_sim=str(self.sim_profile.total_time),
                time_motor=str(self.motor_profile.total_time),
                time_rest=str(self.rest_profile.total_time),
            )
        self.step += 1
        self._setDataPack("control_cmd", {"rate_pos": pos, "rate_neg": neg})
        self.rest_profile.start()

    def shutdown(self):
        self.log.info("NRP Neural Engine: Shutting down.")
        from neural.data_handling import collapse_files

        pop_views = []
        for controller in self.controllers:
            pop_views.extend(controller.get_all_recorded_views())
        collapse_files(self.run_paths.data_nest, pop_views)
        if self.master_config.PLOT_AFTER_SIMULATE:
            plot_controller_outputs(self.run_paths)

        # nest.Cleanup()

    # def reset(self):
    #     self.log.info("NRP Neural Engine: Resetting.")
    #     self.nest_client.Cleanup()

    #     if self.nest_client:
    #         self.nest_client.ResetKernel()

    #     self.initialize()
