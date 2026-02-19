# MUSIC deprecated - this entire file was the MUSIC plant receiver process.
# It has been replaced by NRP coordination (nrp_bullet_engine.py).
#
# #!/usr/bin/env python3
#
# import os
#
# import music
#
# music_setup = music.Setup()
#
# import config.paths as project_paths
# import pybullet as p
# import structlog
# from config.plant_config import PlantConfig
# from mpi4py import MPI
# from plant.plant_simulator import PlantSimulator
# from utils_common.log import setup_logging
#
# from complete_control.plant.plant_plotting import plot_plant_outputs
#
#
# def coordinate_with_simulation():
#     shared_data = {
#         "run_id": None,
#         "paths": None,
#         "parent_id": None,
#     }
#     print("attempting to receive data via broadcast")
#     return MPI.COMM_WORLD.bcast(shared_data, root=0)
#
#
# def main():
#     shared_data = coordinate_with_simulation()
#     run_id: str = shared_data["run_id"]
#     run_paths: project_paths.RunPaths = shared_data["paths"]
#
#     setup_logging(
#         comm=MPI.COMM_WORLD,
#         log_dir_path=run_paths.logs,
#         timestamp_str=run_id,
#         log_level=os.environ.get("LOG_LEVEL", "DEBUG"),
#         default_log_all_ranks=True,
#     )
#     log = structlog.get_logger("receiver_plant.main")
#     log.info(
#         "Receiver plant process started and configured.",
#         world_rank=MPI.COMM_WORLD.Get_rank(),
#         run_id=run_id,
#         log_path=str(run_paths.logs),
#     )
#
#     try:
#         log.info("Initializing PlantSimulator...")
#         config = PlantConfig.from_runpaths(
#             run_paths, parent_id=shared_data["parent_id"]
#         )
#         simulator = PlantSimulator(
#             config=config,
#             pybullet_instance=p,
#             music_setup=music_setup,
#         )
#         log.info("PlantSimulator initialized. Starting simulation run.")
#         simulator.run_simulation()
#         log.info("PlantSimulator run completed.")
#
#     except Exception as e:
#         log.error(
#             "Critical error during plant simulation.", exc_info=True, error=str(e)
#         )
#         MPI.COMM_WORLD.Abort(2)
#     finally:
#         if p.isConnected():
#             log.info("Disconnecting PyBullet from receiver plant.")
#             p.disconnect()
#
#     if config.master_config.plotting.PLOT_AFTER_SIMULATE:
#         plot_plant_outputs(config.run_paths)
#
#     log.info("Receiver plant process finished.")
#
#
# if __name__ == "__main__":
#     main()
