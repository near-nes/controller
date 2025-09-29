#!/usr/bin/env python3
import datetime
import os
from pathlib import Path
from timeit import default_timer as timer

from neural.nest_adapter import initialize_nest, nest

initialize_nest("MUSIC")


import structlog
from config.paths import RunPaths
from mpi4py import MPI
from mpi4py.MPI import Comm
from neural.Controller import Controller
from neural.data_handling import collapse_files, save_conn_weights
from neural.plot_utils import plot_controller_outputs
from utils_common.log import setup_logging

from complete_control.config.core_models import SimulationParams
from complete_control.config.MasterParams import MasterParams
from complete_control.neural.Controller import Controller
from complete_control.neural.data_handling import collapse_files
from complete_control.neural_simulation_lib import (
    create_controllers,
    setup_environment,
    setup_nest_kernel,
)


def run_simulation(
    master_config: MasterParams,
    path_data: Path,
    controllers: list[Controller],
    comm: MPI.Comm,
):
    """Runs the NEST simulation for the specified number of trials."""

    log: structlog.stdlib.BoundLogger = structlog.get_logger(
        "main.simulation_loop", log_all_ranks=True
    )
    single_trial_ms = master_config.simulation.duration_single_trial_ms
    n_trials = master_config.simulation.n_trials

    # --- Prepare for Data Collapsing ---
    pop_views = []
    for controller in controllers:
        pop_views.extend(controller.get_all_recorded_views())

    log.info("collected all popviews")
    controller = controllers[0]
    log.info("Starting Simulation")

    nest.Prepare()
    for trial in range(n_trials):
        current_sim_start_time = nest.GetKernelStatus("biological_time")
        log.info(
            f"Starting Trial {trial + 1}/{n_trials}",
            duration_ms=single_trial_ms,
            current_sim_time_ms=current_sim_start_time,
        )
        log.info(f"Current simulation time: {current_sim_start_time} ms")
        start_trial_time = timer()

        nest.Run(single_trial_ms)

        if controller.use_cerebellum:
            controller.record_synaptic_weights(trial)

        end_trial_time = timer()
        trial_wall_time = datetime.timedelta(seconds=end_trial_time - start_trial_time)
        log.info(
            f"Finished Trial {trial + 1}/{n_trials}",
            sim_time_end_ms=nest.GetKernelStatus("biological_time"),
            wall_time=str(trial_wall_time),
        )
    nest.Cleanup()
    log.info("--- All Trials Finished ---")
    nest.SyncProcesses()

    # --- Data Collapsing (after all trials) ---
    log.info("Attempting data collapsing for all trials...")
    start_collapse_time = timer()
    collapse_files(
        path_data,
        pop_views,
        comm,
    )
    if controller.use_cerebellum and master_config.SAVE_WEIGHTS_CEREB:
        log.info("Saving recorded synapse weights for all trials started...")
        save_conn_weights(
            controller.weights_history,
            path_data,
            "weightrecord",
        )

    end_collapse_time = timer()
    collapse_wall_time = datetime.timedelta(
        seconds=end_collapse_time - start_collapse_time
    )
    log.info(
        "Data collapsing for all trials finished",
        wall_time=str(collapse_wall_time),
    )

    log.info("--- Simulation Finished ---")


def coordinate_paths_with_receiver() -> tuple[str, RunPaths]:
    shared_data = {
        "timestamp": None,
        "paths": None,
    }
    run_timestamp_str = None
    if rank == 0:
        shared_data["timestamp"] = run_timestamp_str = datetime.datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        shared_data["paths"] = RunPaths.from_run_id(run_timestamp_str)
        print("sending paths to all processes...")

    shared_data = MPI.COMM_WORLD.bcast(shared_data, root=0)
    run_timestamp_str = shared_data["timestamp"]
    run_paths: RunPaths = shared_data["paths"]

    return run_timestamp_str, run_paths


if __name__ == "__main__":

    comm = MPI.COMM_WORLD.Create_group(
        MPI.COMM_WORLD.group.Excl([MPI.COMM_WORLD.Get_size() - 1])
    )
    rank = comm.rank
    run_timestamp_str, run_paths = coordinate_paths_with_receiver()
    run_paths = RunPaths.from_run_id(run_timestamp_str)

    setup_logging(
        MPI.COMM_WORLD,
        log_dir_path=run_paths.logs,
        timestamp_str=run_timestamp_str,
        log_level=os.environ.get("LOG_LEVEL", "DEBUG"),
    )

    main_log: structlog.stdlib.BoundLogger = structlog.get_logger("main")
    main_log.info(
        f"Starting Standalone Run: {run_timestamp_str}",
        run_dir=str(run_paths.run),
        log_all_ranks=True,
    )
    main_log.info(
        "MPI Setup Complete (Standalone)",
        world_rank=MPI.COMM_WORLD.Get_rank(),
        world_size=MPI.COMM_WORLD.Get_size(),
        sim_rank=comm.rank,
        sim_size=comm.size,
        log_all_ranks=True,
    )

    start_script_time = timer()

    # Load master config
    master_config = MasterParams.from_runpaths(run_paths=run_paths, USE_MUSIC=True)
    with open(run_paths.params_json, "w") as f:
        f.write(master_config.model_dump_json(indent=2))
    main_log.info("MasterParams initialized in main_simulation (MUSIC).")

    # Setup environment and NEST kernel
    setup_environment(master_config)
    setup_nest_kernel(
        master_config,
        run_paths.data_nest,
    )

    # Create controllers
    controllers = create_controllers(master_config, comm=comm)

    # Run simulation
    run_simulation(master_config, run_paths.data_nest, controllers, comm)

    # Plotting (Rank 0 Only)
    if rank == 0 and master_config.PLOT_AFTER_SIMULATE:
        main_log.info("--- Generating Plots (Standalone) ---")
        start_plot_time = timer()
        plot_controller_outputs(run_paths)
        end_plot_time = timer()
        plot_wall_time = datetime.timedelta(seconds=end_plot_time - start_plot_time)
        main_log.info(f"Plotting Finished (Standalone)", wall_time=str(plot_wall_time))

    # Final Timing
    end_script_time = timer()
    main_log.info(f"--- Script Finished (Standalone) ---")
    main_log.info(
        f"Total wall clock time: {datetime.timedelta(seconds=end_script_time - start_script_time)}"
    )
