"""NRP Neural Engine for the complete control simulation."""

import os

import nest
import structlog
from config.MasterParams import MasterParams
from config.paths import COMPLETE_CONTROL, RunPaths
from config.ResultMeta import extract_id
from neural.nest_adapter import initialize_nest, nest
from neural_simulation_lib import (
    create_controller,
    setup_environment,
    setup_nest_kernel,
)
from nrp_core.engines.python_grpc import GrpcEngineScript
from nrp_protobuf import nrpgenericproto_pb2, wrappers_pb2
from utils_common.profile import Profile

NANO_SEC = 1e-9


class Script(GrpcEngineScript):
    def __init__(self):
        super().__init__()
        self.log = structlog.get_logger("nrp_neural_engine")
        initialize_nest("MUSIC")
        # initialize_nest("NRP")
        self.master_config = None
        self.controller = None
        self.step = 0
        self.run_paths = None

    def initialize(self):
        self.log.info("NRP Neural Engine: Initializing...")
        self.log.debug(nest.GetKernelStatus())
        self.log.debug(nest.ResetKernel())
        self.step = 0

        run_timestamp_str = os.getenv("EXEC_TIMESTAMP")
        parent_id = extract_id(os.getenv("PARENT_ID") or "")

        self.run_paths = RunPaths.from_run_id(run_timestamp_str)
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger("nrp_neural")
        self.log.info(f"Engine Log Path: {self.run_paths.logs}")

        self.master_config = MasterParams.from_runpaths(
            self.run_paths, parent_id=parent_id, USE_MUSIC=False
        )
        with open(self.run_paths.params_json, "w") as f:
            f.write(self.master_config.model_dump_json(indent=2))
        self.log.info("MasterParams loaded and dumped successfully.")

        setup_environment(self.master_config)
        setup_nest_kernel(
            self.master_config,
            self.run_paths.data_nest,
        )
        self.log.info("Environment and NEST kernel setup complete.")

        self.controller = create_controller(self.master_config)
        self.log.info(f"Created controller.")
        self.sensory_profile = Profile()
        self.sim_profile = Profile()
        self.motor_profile = Profile()
        self.rest_profile = Profile()

        # joint_pos_rad (datapack<Double>)
        self._registerDataPack("joint_pos_rad", wrappers_pb2.DoubleValue)
        proto_wrapper = wrappers_pb2.DoubleValue()
        proto_wrapper.value = self.master_config.simulation.oracle.init_joint_angle
        self._setDataPack("joint_pos_rad", proto_wrapper)
        # control_cmd (datapack<Double[]>)
        self._registerDataPack("control_cmd", nrpgenericproto_pb2.ArrayDouble)
        proto_wrapper = nrpgenericproto_pb2.ArrayDouble()
        proto_wrapper.array.extend([0.0, 0.0])
        self._setDataPack("control_cmd", proto_wrapper)

        nest.Prepare()
        self.log.info("NRP Neural Engine: Initialization complete.")

    def runLoop(self, timestep_ns):
        self.rest_profile.end()
        if self.step % 50 == 0:
            self.log.debug("[neural] starting neural update...")

        joint_pos_rad = self._getDataPack("joint_pos_rad").value

        sim_time_s = self._time_ns * NANO_SEC

        with self.sensory_profile.time():
            self.controller.update_sensory_info_from_NRP(
                joint_pos_rad, sim_time_s * 1000
            )

        if self.step % 50 == 0:
            self.log.debug("[neural] updated sensory info")

        with self.sim_profile.time():
            nest.Run(timestep_ns * NANO_SEC * 1000)

        if self.step % 50 == 0:
            self.log.debug("[neural] simulated")

        with self.motor_profile.time():
            pos, neg = self.controller.extract_motor_command_NRP()

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

        datapack = nrpgenericproto_pb2.ArrayDouble()
        datapack.array.extend([pos, neg])
        self._setDataPack("control_cmd", datapack)

        self.rest_profile.start()

    def shutdown(self):
        self.log.info(
            f"[neural] Simulation complete.",
            time_sensory=str(self.sensory_profile.total_time),
            time_sim=str(self.sim_profile.total_time),
            time_motor=str(self.motor_profile.total_time),
            time_rest=str(self.rest_profile.total_time),
        )
        from neural.data_handling import collapse_files, save_conn_weights

        rec_paths = None
        if self.controller.use_cerebellum and self.master_config.SAVE_WEIGHTS_CEREB:
            w = self.controller.record_synaptic_weights()
            rec_paths = save_conn_weights(w, self.run_paths.data_nest, comm=None)

        pop_views = self.controller.collect_populations()
        res = collapse_files(self.run_paths.data_nest, pop_views)
        res.weights = rec_paths

        with open(self.master_config.run_paths.neural_result, "w") as f:
            f.write(res.model_dump_json())

        # nest.Cleanup()
