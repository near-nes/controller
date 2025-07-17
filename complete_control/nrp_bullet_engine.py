""" """

import datetime

import config.paths as project_paths
import pybullet as p
import structlog
from config.plant_config import PlantConfig
from nrp_core.engines.python_json import EngineScript
from plant.plant_simulator import PlantSimulator


class Script(EngineScript):

    def __init__(self):
        super().__init__()

    def initialize(self):
        print("PyBullet Engine Server is initializing.")
        run_timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_paths = project_paths.RunPaths.from_run_id(run_timestamp_str)
        # TODO adapt logging for serial
        log: structlog.stdlib.BoundLogger = structlog.get_logger("receiver_plant.main")
        log.info(
            "Receiver plant process started and configured.",
            run_timestamp=run_timestamp_str,
        )
        self.config = PlantConfig.from_runpaths(self.run_paths)

        self.simulator = PlantSimulator(
            config=self.config,
            pybullet_instance=p,
            music_setup=None,
        )
        self.current_sim_time_s = 0
        self.step = 0
        log.info("PlantSimulator initialized.")

        self._registerDataPack("positions")
        self._registerDataPack("control_cmd")

        log.info("DataPacks registered.")

        self._setDataPack(
            "positions",
            {"joint_pos_rad": self.config.master_config.experiment.init_joint_angle},
        )

    def runLoop(self, timestep):
        print("timestep = ", timestep)
        #  Receive control data
        ctrl = self._getDataPack("control_cmd")
        rate_pos = ctrl["rate_pos"]
        rate_neg = ctrl["rate_neg"]

        joint_pos_rad, joint_vel, ee_pos, ee_vel = self.simulator.run_simulation_step(
            rate_pos, rate_neg, self.current_sim_time_s, self.step
        )
        self.current_sim_time_s += self.config.RESOLUTION_S
        self.step += 1

        self._setDataPack("positions", {"joint_pos_rad": joint_pos_rad})

    def shutdown(self):
        print("Simulation End !!!")
