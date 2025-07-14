""" """

import datetime
import os

import music

music_setup = music.Setup()
# i know, this is weird. it's the only order in which i could manage to make music
# play nice with nest and mpi. if you want to change it, go ahead, but make sure it
# works before pushing

import config.paths as project_paths
import pybullet as p
import structlog
from config.plant_config import PlantConfig
from nrp_core.engines.python_json import EngineScript
from plant.plant_simulator import PlantSimulator
from utils_common.log import setup_logging


class Script(EngineScript):

    def __init__(self):
        super().__init__()
        self.initialize()

    def initialize(self):
        print("PyBullet Engine Server is initializing.")
        run_timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_paths = project_paths.RunPaths.from_run_id(run_timestamp_str)

        setup_logging(
            comm=None,
            log_dir_path=self.run_paths.logs,
            timestamp_str=run_timestamp_str,
            log_level=os.environ.get("LOG_LEVEL", "DEBUG"),
        )
        log: structlog.stdlib.BoundLogger = structlog.get_logger("receiver_plant.main")
        log.info(
            "Receiver plant process started and configured.",
            run_timestamp=run_timestamp_str,
        )
        self.config = PlantConfig.from_runpaths(self.run_paths)

        self.simulator = PlantSimulator(
            config=self.config,
            pybullet_instance=p,
            music_setup=music_setup,
        )
        self.current_sim_time_s = 0
        self.step = 0
        log.info("PlantSimulator initialized. Starting simulation run.")

        self._registerDataPack("positions")

        self._registerDataPack("control_cmd")
        print("DataPacks registered.")

        self._setDataPack(
            "positions",
            {"joint_pos_rad": self.config.master_config.experiment.init_joint_angle},
        )

    def runLoop(self, timestep):
        print("timestep = ", timestep)
        #  Receive control data
        rate_pos = self._getDataPack("control_cmd").get("rate_pos")
        rate_neg = self._getDataPack("control_cmd").get("rate_neg")

        joint_pos_rad, joint_vel, ee_pos, ee_vel = self.simulator.run_simulation_step(
            rate_pos, rate_neg, self.current_sim_time_s, self.step
        )
        self.current_sim_time_s += self.config.RESOLUTION_S
        self.step += 1

        self._setDataPack("positions", {"joint_pos_rad": joint_pos_rad})

    def shutdown(self):
        self.sim_manager.shutdown()
        print("Simulation End !!!")
