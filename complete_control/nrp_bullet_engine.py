""" """

import os

import config.paths as project_paths
import pybullet as p
import structlog
from config.plant_config import PlantConfig
from nrp_core.engines.python_grpc import GrpcEngineScript
from nrp_protobuf import nrpgenericproto_pb2, wrappers_pb2
from plant.plant_plotting import plot_plant_outputs
from plant.plant_simulator import PlantSimulator, TrialSection
from utils_common.profile import Profile


class Script(GrpcEngineScript):

    def __init__(self):
        super().__init__()
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger(
            "nrp_neural_engine"
        )

    def initialize(self):
        self.log.info("PyBullet Engine Server is initializing.")
        run_timestamp_str = os.getenv("EXEC_TIMESTAMP")
        self.log.warning(f"run_timestamp_str =<{run_timestamp_str}>")
        self.run_paths = project_paths.RunPaths.from_run_id(run_timestamp_str)
        self.config = PlantConfig.from_runpaths(self.run_paths)

        self.simulator = PlantSimulator(
            config=self.config,
            pybullet_instance=p,
            music_setup=None,
        )
        self.current_sim_time_s = 0
        self.step = 0
        self.pybullet_profile = Profile()
        self.rest_profile = Profile()
        self.log.info("PlantSimulator initialized.")

        # joint_pos_rad (datapack<Double>)
        self._registerDataPack("joint_pos_rad", wrappers_pb2.DoubleValue)
        proto_wrapper = wrappers_pb2.DoubleValue()
        proto_wrapper.value = (
            self.config.master_config.simulation.oracle.init_joint_angle
        )
        self._setDataPack("joint_pos_rad", proto_wrapper)
        # control_cmd (datapack<Double[]>)
        self._registerDataPack("control_cmd", nrpgenericproto_pb2.ArrayDouble)
        proto_wrapper = nrpgenericproto_pb2.ArrayDouble()
        proto_wrapper.array.extend([0.0, 0.0])
        self._setDataPack("control_cmd", proto_wrapper)

        self.log.info("NRP Bullet Engine: Initialization complete.")

    def runLoop(self, timestep):
        self.rest_profile.end()
        if self.step % 50 == 0:
            self.log.debug("[bullet] starting update...")
        ctrl = self._getDataPack("control_cmd").array
        rate_pos, rate_neg = ctrl[0], ctrl[1]

        with self.pybullet_profile.time():
            joint_pos_rad, joint_vel, ee_pos, ee_vel, curr_section = (
                self.simulator.run_simulation_step(
                    rate_pos, rate_neg, self.current_sim_time_s, self.step
                )
            )

        if curr_section == TrialSection.TIME_POST:
            joint_pos_rad = 0.0  # mask joint position during TIME_POST

        self.current_sim_time_s += self.config.RESOLUTION_S
        self.step += 1
        if self.step % 50 == 0:
            self.log.debug(
                f"[bullet] Update {self.step} complete.",
                joint_pos=joint_pos_rad,
                rate_pos=rate_pos,
                rate_neg=rate_neg,
                time_pybullet=str(self.pybullet_profile.total_time),
                time_rest=str(self.rest_profile.total_time),
            )

        datapack = wrappers_pb2.DoubleValue()
        datapack.value = joint_pos_rad
        self._setDataPack("joint_pos_rad", datapack)

        self.rest_profile.start()

    def shutdown(self):
        self.log.info("Simulation loop finished.")
        self.simulator._finalize_and_process_data()
        if self.config.master_config.plotting.PLOT_AFTER_SIMULATE:
            plot_plant_outputs(self.run_paths)
        print("Simulation End !!!")
