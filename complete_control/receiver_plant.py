#!/usr/bin/env python3

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
from mpi4py import MPI
from plant.plant_simulator import PlantSimulator
from utils_common.log import setup_logging

from complete_control.plant.plant_plotting import plot_plant_outputs


def coordinate_with_simulation():
    shared_data = {
        "timestamp": None,
        "paths": None,
    }
    print("attempting to receive data via broadcast")
    return MPI.COMM_WORLD.bcast(shared_data, root=0)


def main():
    shared_data = coordinate_with_simulation()
    run_timestamp_str: str = shared_data["timestamp"]
    run_paths: project_paths.RunPaths = shared_data["paths"]

    setup_logging(
        comm=MPI.COMM_WORLD,
        log_dir_path=run_paths.logs,
        timestamp_str=run_timestamp_str,
        log_level=os.environ.get("LOG_LEVEL", "DEBUG"),
        default_log_all_ranks=True,
    )
    log = structlog.get_logger("receiver_plant.main")
    log.info(
        "Receiver plant process started and configured.",
        world_rank=MPI.COMM_WORLD.Get_rank(),
        run_timestamp=run_timestamp_str,
        log_path=str(run_paths.logs),
    )

    try:
        log.info("Initializing PlantSimulator...")
        config = PlantConfig.from_runpaths(run_paths)
        simulator = PlantSimulator(
            config=config,
            pybullet_instance=p,
            music_setup=music_setup,
        )
        log.info("PlantSimulator initialized. Starting simulation run.")
        simulator.run_simulation()
        log.info("PlantSimulator run completed.")

    except Exception as e:
        log.error(
            "Critical error during plant simulation.", exc_info=True, error=str(e)
        )
        # Ensure MPI aborts if a critical error occurs in this process
        MPI.COMM_WORLD.Abort(2)  # Use a different error code
    finally:
        if p.isConnected():  # Check if a connection was made by RoboticPlant
            log.info("Disconnecting PyBullet from receiver plant.")
            p.disconnect()

    if config.master_config.plotting.PLOT_AFTER_SIMULATE:
        plot_plant_outputs(config.run_paths)

    log.info("Receiver plant process finished.")


if __name__ == "__main__":
    main()
