#!/usr/bin/env python3
import datetime
import os
from pathlib import Path
from timeit import default_timer as timer

from neural.nest_adapter import initialize_nest, nest

initialize_nest("MUSIC")


import structlog
from config.MasterParams import MasterParams
from config.paths import RunPaths
from config.ResultMeta import ResultMeta, extract_id
from mpi4py import MPI
from neural.Controller import Controller
from neural.data_handling import collapse_files, save_conn_weights
from neural.plot_utils import plot_controller_outputs
from neural_simulation_lib import (
    create_controller,
    setup_environment,
    setup_nest_kernel,
)
from utils_common.log import setup_logging
from utils_common.results import make_trial_id


def run_simulation(
    master_config: MasterParams,
    path_data: Path,
    controller: Controller,
    comm: MPI.Comm,
):
    """Runs the NEST simulation for the specified number of trials."""

    log: structlog.stdlib.BoundLogger = structlog.get_logger(
        "main.simulation_loop", log_all_ranks=True
    )

    log.info("collected all popviews")
    log.info("Starting Simulation")
    ###############################
    log.info("Waiting for all MPI ranks to finish MUSIC port setup before Prepare")
    MPI.COMM_WORLD.barrier()
    ###############################
    nest.Prepare()
    current_sim_start_time = nest.GetKernelStatus("biological_time")
    log.info(f"Current simulation time: {current_sim_start_time} ms")

    nest.Run(master_config.simulation.duration_ms)

    rec_paths = None
    if controller.use_cerebellum and master_config.SAVE_WEIGHTS_CEREB:
        w = controller.record_synaptic_weights()
        rec_paths = save_conn_weights(w, path_data, comm)

    nest.Cleanup()

    log.info("Attempting data collapsing...")
    start_collapse_time = timer()
    res = collapse_files(
        path_data,
        controller.collect_populations(),
        comm,
    )
    res.weights = rec_paths  # TODO move this somewhere less ugly

    if rank == 0:
        with open(master_config.run_paths.neural_result, "w") as f:
            f.write(res.model_dump_json())

    end_collapse_time = timer()
    collapse_wall_time = datetime.timedelta(
        seconds=end_collapse_time - start_collapse_time
    )
    log.info(
        "Data collapsing finished",
        wall_time=str(collapse_wall_time),
    )

    if rank == 0:
        result = ResultMeta.create(master_config)
        result.save(master_config.run_paths)

    log.info("--- Simulation Finished ---")


def coordinate_paths_with_receiver(
    label: str = "", parent_id: str = ""
) -> tuple[str, RunPaths]:
    shared_data = {
        "run_id": None,
        "paths": None,
        "parent_id": None,
    }
    run_id = None
    if rank == 0:
        run_id = make_trial_id(
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S"), label=label
        )
        shared_data["run_id"] = run_id
        shared_data["paths"] = RunPaths.from_run_id(run_id)
        shared_data["parent_id"] = parent_id
        print("sending paths to all processes...")
        print(f"__SIMULATION_RUN_ID__:{run_id}", flush=True)

    shared_data = MPI.COMM_WORLD.bcast(shared_data, root=0)
    run_id = shared_data["run_id"]
    run_paths: RunPaths = shared_data["paths"]

    return run_id, run_paths


def generate_param_plot(data, pop_name, param_name, plots_path, plot_one_n=True):
    import matplotlib.pyplot as plt
    import numpy as np

    senders = np.array(data["senders"])
    times = np.array(data["times"])
    param = np.array(data[param_name])

    fig = plt.figure(figsize=(10, 6))

    # take one neuron (id=sender)
    if plot_one_n:
        gid = np.unique(senders)[0]
        mask = senders == gid
        plt.plot(times[mask], param[mask])
        plt.title(f"{pop_name} - {param_name} - neuron {gid}")
        # if param_name == "CV_fbk" or param_name == "CV_pred":
        #    plt.ylim(0, 1)

    # plot all neurons
    else:
        for gid in np.unique(senders):
            mask = senders == gid
            plt.plot(
                times[mask], param[mask], color=(0, 0, 0, 0.05), label=f"Neuron {gid}"
            )
        plt.title(f"{pop_name} - {param_name} - all neurons")
        # plt.legend()

    plt.xlabel("Time (ms)")
    plt.ylabel(param_name)

    fig.savefig(plots_path / f"{pop_name}_{param_name}.png")
    plt.close(fig)
    return


if __name__ == "__main__":
    parent_id = extract_id(os.environ.get("PARENT_ID") or "")
    # 20251112_142047_7bri-singletrial

    comm = MPI.COMM_WORLD.Create_group(
        MPI.COMM_WORLD.group.Excl([MPI.COMM_WORLD.Get_size() - 1])
    )
    rank = comm.rank
    label = "singletrial"
    run_id, run_paths = coordinate_paths_with_receiver(label, parent_id)
    run_paths = RunPaths.from_run_id(run_id)

    setup_logging(
        MPI.COMM_WORLD,
        log_dir_path=run_paths.logs,
        timestamp_str=run_id,
        log_level=os.environ.get("LOG_LEVEL", "DEBUG"),
    )

    main_log: structlog.stdlib.BoundLogger = structlog.get_logger("main")
    main_log.info(
        f"Starting Standalone Run: {run_id}",
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

    master_config = MasterParams.from_runpaths(run_paths, parent_id, USE_MUSIC=True)
    master_config.save_to_json(run_paths.params_json)
    main_log.info("MasterParams initialized in music_start_sim (MUSIC).")

    # Setup environment and NEST kernel
    setup_environment(master_config)
    setup_nest_kernel(
        master_config,
        run_paths.data_nest,
    )

    controller = create_controller(master_config, comm=comm)

    run_simulation(master_config, run_paths.data_nest, controller, comm)
    # #######################################################
    # # create and connect mm to state
    # params_state = [
    #     "var_fbk",
    #     "var_pred",
    #     "mean_fbk",
    #     "mean_pred",
    #     "w_fbk",
    #     "w_pred",
    #     "CV_fbk",
    #     "CV_pred",
    # ]
    # mm_state = nest.Create("multimeter", {"record_from": params_state})
    # nest.Connect(mm_state, controllers[0].pops.state_p.pop)

    # mm_pred = nest.Create("multimeter", 1, {"record_from": ["lambda_poisson"]})
    # mm_fbk = nest.Create("multimeter", 1, {"record_from": ["lambda_poisson"]})
    # for x in range(200):
    #     if (
    #         "lambda_poisson"
    #         in nest.GetStatus(controllers[0].pops.pred_p.pop[x])[0].keys()
    #     ):
    #         nest.Connect(mm_pred, controllers[0].pops.pred_p.pop[x])
    #     else:
    #         print(f"Neuron pred {x} has not been connected")
    # for x in range(200):
    #     if (
    #         "lambda_poisson"
    #         in nest.GetStatus(controllers[0].pops.fbk_smooth_p.pop[x])[0].keys()
    #     ):
    #         nest.Connect(mm_fbk, controllers[0].pops.fbk_smooth_p.pop[x])
    #     else:
    #         print(f"Neuron fbk_smooth {x} has not been connected")

    # print(
    #     f"Dcn params: {nest.GetStatus(controllers[0].cerebellum_handler.cerebellum.populations.forw_dcnp_p_view.pop[0])[0].keys()}"
    # )
    # ##############################################################

    # # Run simulation
    # run_simulation(master_config, run_paths.data_nest, controllers, comm)

    # ##########################à

    # main_log.info("Start - Params from mm printed successfully")
    # pop_name = "State_Estimator"
    # plots_path = run_paths.figures
    # data_state = nest.GetStatus(mm_state, "events")[0]
    # data_pred = nest.GetStatus(mm_pred, "events")[0]
    # data_fbk = nest.GetStatus(mm_fbk, "events")[0]
    # for param in params_state:
    #     try:
    #         generate_param_plot(
    #             data_state, pop_name, param, plots_path, plot_one_n=True
    #         )
    #     except Exception as e:
    #         print(f"Error: {e}, \n param_: {param}")
    # try:
    #     pop_name = "Pred"
    #     param = "lambda_poisson"
    #     generate_param_plot(data_pred, pop_name, param, plots_path, plot_one_n=False)
    #     pop_name = "FbkSmooth"
    #     generate_param_plot(data_fbk, pop_name, param, plots_path, plot_one_n=False)
    # except Exception as e:
    #     print(f"Pred Error: {e} \n")
    # main_log.info("Params from mm printed successfully")

    # ###############################################################

    # Plotting (Rank 0 Only)
    if rank == 0 and master_config.plotting.PLOT_AFTER_SIMULATE:
        main_log.info("--- Generating Plots (Standalone) ---")
        start_plot_time = timer()
        plot_controller_outputs(run_paths)
        end_plot_time = timer()
        plot_wall_time = datetime.timedelta(seconds=end_plot_time - start_plot_time)
        main_log.info(f"Plotting Finished (Standalone)", wall_time=str(plot_wall_time))

    end_script_time = timer()
    main_log.info(f"--- Script Finished (Standalone) ---")
    main_log.info(
        f"Total wall clock time: {datetime.timedelta(seconds=end_script_time - start_script_time)}"
    )
