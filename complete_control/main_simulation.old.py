#!/usr/bin/env python3

import datetime
import json
import os
import random
import shutil
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from timeit import default_timer as timer

import config.paths as paths
import nest
import numpy as np
import structlog
from config.paths import RunPaths
from mpi4py import MPI
from mpi4py.MPI import Comm
from neural.Controller import Controller
from neural.data_handling import collapse_files
from neural.plot_utils import plot_controller_outputs
from utils_common.generate_analog_signals import generate_signals
from utils_common.log import setup_logging, tqdm

from complete_control.config.core_models import MetaInfo, SimulationParams
from complete_control.config.MasterParams import MasterParams

nest.set_verbosity("M_ERROR")  # M_WARNING


# --- Configuration and Setup ---
def setup_environment(nestml_build_dir=paths.NESTML_BUILD_DIR):
    log = structlog.get_logger("main.env_setup")
    """Sets up environment variables if needed (e.g., for NESTML)."""
    try:
        # Check if module is already installed to prevent errors on reset
        if "eglif_cond_alpha_multisyn" not in nest.Models(mtype="nodes"):
            nest.Install("custom_stdp_module")
            log.info("Installed NESTML module", module="custom_stdp_module")
        else:
            log.debug("NESTML module already installed", module="custom_stdp_module")
    except nest.NESTError as e:
        log.error(
            "Error installing NESTML module",
            module="custom_stdp_module",
            error=str(e),
            exc_info=True,
        )
        log.error(
            "Ensure module is compiled and accessible (check LD_LIBRARY_PATH/compilation)."
        )
        sys.exit(1)


# --- NEST Kernel Setup ---
def setup_nest_kernel(simulation_config: SimulationParams, seed: int, path_data: Path):
    log = structlog.get_logger("main.nest_setup")
    """Configures the NEST kernel."""

    kernel_status = {
        "resolution": simulation_config.resolution,
        "overwrite_files": True,  # optional since different data paths
        "data_path": str(path_data),
        # "print_time": True, # Optional: Print simulation progress
    }
    kernel_status["rng_seed"] = seed  # Set seed via kernel status
    nest.SetKernelStatus(kernel_status)
    log.info(
        f"NEST Kernel: Resolution: {simulation_config.resolution}ms, Seed: {seed}, Data path: {str(path_data)}"
    )
    random.seed(seed)
    np.random.seed(seed)


def run_simulation(
    simulation_config: SimulationParams,
    path_data: Path,
    controllers: list[Controller],
    comm: Comm,
):
    log: structlog.stdlib.BoundLogger = structlog.get_logger("main.simulation_loop")
    """Runs the NEST simulation for the specified number of trials."""
    single_trial_ms = simulation_config.duration_single_trial_ms
    n_trials = simulation_config.n_trials

    # --- Prepare for Data Collapsing ---
    pop_views = []
    for controller in controllers:
        pop_views.extend(controller.get_all_recorded_views())

    log.info("collected all popviews")
    with nest.RunManager():
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

            end_trial_time = timer()
            trial_wall_time = timedelta(seconds=end_trial_time - start_trial_time)
            log.info(
                f"Finished Trial {trial + 1}/{n_trials}",
                sim_time_end_ms=nest.GetKernelStatus("biological_time"),
                wall_time=str(trial_wall_time),
            )

    log.info("--- All Trials Finished ---")

    # --- Data Collapsing (after all trials) ---
    log.info("Attempting data collapsing for all trials...")
    start_collapse_time = timer()
    collapse_files(
        path_data,
        pop_views,
        comm,
    )

    end_collapse_time = timer()
    collapse_wall_time = timedelta(seconds=end_collapse_time - start_collapse_time)
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
    # --- Setup ---
    comm = MPI.COMM_WORLD.Create_group(  # last process is for receiver_plant
        MPI.COMM_WORLD.group.Excl([MPI.COMM_WORLD.Get_size() - 1])
    )
    rank = comm.rank
    run_timestamp_str, run_paths = coordinate_paths_with_receiver()
    setup_logging(
        MPI.COMM_WORLD,
        log_dir_path=run_paths.logs,
        timestamp_str=run_timestamp_str,
        log_level=os.environ.get("LOG_LEVEL", "DEBUG"),
    )

    main_log: structlog.stdlib.BoundLogger = structlog.get_logger("main")
    main_log.info(
        f"Starting Run: {run_timestamp_str}",
        run_dir=str(run_paths.run),
        log_all_ranks=True,
    )
    main_log.info(
        "MPI Setup Complete",
        world_rank=MPI.COMM_WORLD.Get_rank(),
        world_size=MPI.COMM_WORLD.Get_size(),
        sim_rank=comm.rank,
        sim_size=comm.size,
        log_all_ranks=True,
    )

    start_script_time = timer()
    nest.ResetKernel()
    master_config = MasterParams.from_runpaths(run_paths=run_paths)
    run_id = master_config.run_paths.run.name

    with open(run_paths.params_json, "w") as f:
        f.write(master_config.model_dump_json(indent=2))

    main_log.info("MasterParams initialized in music_start_sim.")

    module_params = master_config.modules
    pops_params = master_config.populations
    conn_params = master_config.connections

    main_log.debug(
        "MasterConfig loaded via PlantConfig",
        master_config_dump=master_config.model_dump_json(indent=2),
    )

    N = master_config.brain.population_size
    njt = master_config.NJT

    setup_environment()

    trj, motor_commands = generate_signals(
        master_config.experiment, master_config.simulation
    )

    main_log.info(f"Using {njt} DoF based on PlantConfig.")
    main_log.info("Input data (trajectory, motor_commands) generated.", dof=njt)

    res = master_config.simulation.resolution
    time_span_per_trial = master_config.simulation.duration_single_trial_ms
    n_trials = master_config.simulation.n_trials
    total_sim_duration = master_config.simulation.total_duration_all_trials_ms

    single_trial_time_vect = np.linspace(
        0,
        time_span_per_trial,
        num=int(np.round(time_span_per_trial / res)),
        endpoint=True,
    )
    # Total time vector across all trials (for plotting concatenated results)
    total_time_vect_concat = np.linspace(
        0,
        total_sim_duration,
        num=int(np.round(total_sim_duration / res)),
        endpoint=True,
    )

    main_log.debug(
        "Time vectors calculated",
        total_duration=total_sim_duration,
        single_trial_duration=time_span_per_trial,
        num_steps_total=len(total_time_vect_concat),
        num_steps_trial=len(single_trial_time_vect),
    )

    # --- Network Construction ---
    start_network_time = timer()
    setup_nest_kernel(
        master_config.simulation, master_config.simulation.seed, run_paths.data_nest
    )

    controllers = []
    main_log.info(f"Constructing Network", dof=njt, N_neurons_pop=N)
    for j in range(njt):
        main_log.info(f"Creating controller", dof=j)

        controller = Controller(
            dof_id=j,
            N=N,
            total_time_vect=total_time_vect_concat,
            trajectory_slice=trj,
            motor_cmd_slice=motor_commands,
            mc_params=module_params.motor_cortex,
            plan_params=module_params.planner,
            spine_params=module_params.spine,
            state_params=module_params.state,
            pops_params=pops_params,
            conn_params=conn_params,
            sim_params=master_config.simulation,
            path_data=run_paths.data_nest,
            label_prefix="",
            music_cfg=master_config.music,
            use_cerebellum=master_config.USE_CEREBELLUM,
            cerebellum_paths=master_config.bsb_config_paths,
            comm=comm,
        )
        controllers.append(controller)

    end_network_time = timer()
    main_log.info(
        f"Network Construction Finished",
        wall_time=str(timedelta(seconds=end_network_time - start_network_time)),
    )

    # --- Simulation ---
    # Pass simulation_config from master_config to run_simulation
    run_simulation(master_config.simulation, run_paths.data_nest, controllers, comm)

    # --- Plotting (Rank 0 Only) ---
    if rank == 0 and master_config.PLOT_AFTER_SIMULATE:
        main_log.info("--- Generating Plots ---")
        start_plot_time = timer()
        plot_controller_outputs(run_paths)
        end_plot_time = timer()
        plot_wall_time = timedelta(seconds=end_plot_time - start_plot_time)
        main_log.info(f"Plotting Finished", wall_time=str(plot_wall_time))

    # --- Final Timing ---
    end_script_time = timer()
    main_log.info(f"--- Script Finished ---")
    main_log.info(
        f"Total wall clock time: {timedelta(seconds=end_script_time - start_script_time)}"
    )
