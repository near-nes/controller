""" """

import os

import config.paths as project_paths
import pybullet as p
import structlog
from config.plant_config import PlantConfig
from nrp_core.engines.python_json import EngineScript
from plant.plant_simulator import PlantSimulator
from utils_common.profile import Profile


class Script(EngineScript):

    def __init__(self):
        super().__init__()
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger(
            "nrp_neural_engine"
        )

    def initialize(self):
        print("PyBullet Engine Server is initializing.")
        run_timestamp_str = os.getenv("EXEC_TIMESTAMP")
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

        self._registerDataPack("positions")
        self._registerDataPack("control_cmd")

        self.log.info("DataPacks registered.")

        self._setDataPack(
            "positions",
            {"joint_pos_rad": self.config.master_config.experiment.init_joint_angle},
        )
        self.log.info("NRP Bullet Engine: Initialization complete.")

    def runLoop(self, timestep):
        self.rest_profile.end()
        if self.step % 50 == 0:
            self.log.debug("[bullet] starting update...")
        ctrl = self._getDataPack("control_cmd")
        rate_pos = ctrl["rate_pos"]
        rate_neg = ctrl["rate_neg"]

        with self.pybullet_profile.time():
            joint_pos_rad, joint_vel, ee_pos, ee_vel = (
                self.simulator.run_simulation_step(
                    rate_pos, rate_neg, self.current_sim_time_s, self.step
                )
            )

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

        self._setDataPack("positions", {"joint_pos_rad": joint_pos_rad})
        self.rest_profile.start()

    def shutdown(self):
        self.log.info("Simulation loop finished.")
        self.simulator._finalize_and_process_data()
        print("Simulation End !!!")
