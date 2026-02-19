# MUSIC deprecated - this entire file was the MUSIC neural simulation entry point.
# It has been replaced by NRP coordination (nrp_neural_engine.py + nrp_start_sim.py).
#
# #!/usr/bin/env python3
# import datetime
# import os
# from pathlib import Path
# from timeit import default_timer as timer
#
# from neural.nest_adapter import initialize_nest, nest
#
# initialize_nest("MUSIC")
#
#
# import structlog
# from config.MasterParams import MasterParams
# from config.paths import RunPaths
# from config.ResultMeta import ResultMeta, extract_id
# from mpi4py import MPI
# from neural.Controller import Controller
# from neural.data_handling import collapse_files, save_conn_weights
# from neural.plot_utils import plot_controller_outputs
# from neural_simulation_lib import (
#     create_controller,
#     setup_environment,
#     setup_nest_kernel,
# )
# from utils_common.log import setup_logging
# from utils_common.results import make_trial_id
#
#
# def run_simulation(
#     master_config: MasterParams,
#     path_data: Path,
#     controller: Controller,
#     comm: MPI.Comm,
# ):
#     """Runs the NEST simulation for the specified number of trials."""
#
#     log: structlog.stdlib.BoundLogger = structlog.get_logger(
#         "main.simulation_loop", log_all_ranks=True
#     )
#
#     log.info("collected all popviews")
#     log.info("Starting Simulation")
#     log.info("Waiting for all MPI ranks to finish MUSIC port setup before Prepare")
#     MPI.COMM_WORLD.barrier()
#     nest.Prepare()
#     current_sim_start_time = nest.GetKernelStatus("biological_time")
#     log.info(f"Current simulation time: {current_sim_start_time} ms")
#
#     nest.Run(master_config.simulation.duration_ms)
#
#     rec_paths = None
#     log.info(f"Simulation completed, saving weights...")
#     if controller.use_cerebellum and master_config.SAVE_WEIGHTS_CEREB:
#         w = controller.record_synaptic_weights()
#         rec_paths = save_conn_weights(w, path_data, comm)
#
#     nest.Cleanup()
#
#     log.info("Attempting data collapsing...")
#     start_collapse_time = timer()
#     res = collapse_files(
#         path_data,
#         controller.collect_populations(),
#         comm,
#     )
#     res.weights = rec_paths
#
#     if rank == 0:
#         with open(master_config.run_paths.neural_result, "w") as f:
#             f.write(res.model_dump_json())
#
#     end_collapse_time = timer()
#     collapse_wall_time = datetime.timedelta(
#         seconds=end_collapse_time - start_collapse_time
#     )
#     log.info(
#         "Data collapsing finished",
#         wall_time=str(collapse_wall_time),
#     )
#
#     if rank == 0:
#         result = ResultMeta.create(master_config)
#         result.save(master_config.run_paths)
#
#     log.info("--- Simulation Finished ---")
#
#
# def coordinate_paths_with_receiver(
#     label: str = "", parent_id: str = ""
# ) -> tuple[str, RunPaths]:
#     shared_data = {
#         "run_id": None,
#         "paths": None,
#         "parent_id": None,
#     }
#     run_id = None
#     if rank == 0:
#         run_id = make_trial_id(
#             datetime.datetime.now().strftime("%Y%m%d_%H%M%S"), label=label
#         )
#         shared_data["run_id"] = run_id
#         shared_data["paths"] = RunPaths.from_run_id(run_id)
#         shared_data["parent_id"] = parent_id
#         print("sending paths to all processes...")
#         print(f"__SIMULATION_RUN_ID__:{run_id}", flush=True)
#
#     shared_data = MPI.COMM_WORLD.bcast(shared_data, root=0)
#     run_id = shared_data["run_id"]
#     run_paths: RunPaths = shared_data["paths"]
#
#     return run_id, run_paths
#
#
# if __name__ == "__main__":
#     parent_id = extract_id(os.environ.get("PARENT_ID") or "")
#
#     comm = MPI.COMM_WORLD.Create_group(
#         MPI.COMM_WORLD.group.Excl([MPI.COMM_WORLD.Get_size() - 1])
#     )
#     rank = comm.rank
#     label = "singletrial"
#     run_id, run_paths = coordinate_paths_with_receiver(label, parent_id)
#     run_paths = RunPaths.from_run_id(run_id)
#
#     setup_logging(
#         MPI.COMM_WORLD,
#         log_dir_path=run_paths.logs,
#         timestamp_str=run_id,
#         log_level=os.environ.get("LOG_LEVEL", "DEBUG"),
#     )
#
#     main_log: structlog.stdlib.BoundLogger = structlog.get_logger("main")
#     main_log.info(
#         f"Starting Standalone Run: {run_id}",
#         run_dir=str(run_paths.run),
#         log_all_ranks=True,
#     )
#
#     start_script_time = timer()
#
#     master_config = MasterParams.from_runpaths(run_paths, parent_id, USE_MUSIC=True)
#     master_config.save_to_json(run_paths.params_json)
#     main_log.info("MasterParams initialized in music_start_sim (MUSIC).")
#
#     setup_environment(master_config)
#     setup_nest_kernel(
#         master_config,
#         run_paths.data_nest,
#     )
#
#     controller = create_controller(master_config, comm=comm)
#
#     run_simulation(master_config, run_paths.data_nest, controller, comm)
#
#     if rank == 0 and master_config.plotting.PLOT_AFTER_SIMULATE:
#         main_log.info("--- Generating Plots (Standalone) ---")
#         start_plot_time = timer()
#         plot_controller_outputs(run_paths)
#         end_plot_time = timer()
#         plot_wall_time = datetime.timedelta(seconds=end_plot_time - start_plot_time)
#         main_log.info(f"Plotting Finished (Standalone)", wall_time=str(plot_wall_time))
#
#     end_script_time = timer()
#     main_log.info(f"--- Script Finished (Standalone) ---")
#     main_log.info(
#         f"Total wall clock time: {datetime.timedelta(seconds=end_script_time - start_script_time)}"
#     )
