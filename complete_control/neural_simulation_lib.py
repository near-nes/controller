import random
import sys
from pathlib import Path
from timeit import default_timer as timer

import config.paths as paths
import numpy as np
import structlog
from config.core_models import SimulationParams
from config.MasterParams import MasterParams
from neural.Controller import Controller
from neural.nest_adapter import nest

# nest.set_verbosity("M_ERROR") # TOCHECK: Verbosity might be set by NEST server


# --- Configuration and Setup ---
def setup_environment():
    log = structlog.get_logger("main.env_setup")
    """Sets up environment variables if needed (e.g., for NESTML)."""
    try:
        # Check if module is already installed to prevent errors on reset
        if "eglif_cond_alpha_multisyn" not in nest.Models(mtype="nodes"):
            nest.Install("custom_stdp_module")
            log.info("Installed NESTML module", module="custom_stdp_module")
        else:
            log.debug("NESTML module already installed", module="custom_stdp_module")
    except (
        Exception
    ) as e:  # TOCHECK: Changed to generic Exception as nest.NESTError might not be available
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
def setup_nest_kernel(
    simulation_config: SimulationParams,
    seed: int,
    path_data: Path,
):
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


def create_controllers(
    master_config: MasterParams,
    trj: np.ndarray,
    motor_commands: np.ndarray,
    # comm: Comm, # TOCHECK: MPI removed
) -> list[Controller]:
    log = structlog.get_logger("main.network_construction")
    module_params = master_config.modules
    pops_params = master_config.populations
    conn_params = master_config.connections

    N = master_config.brain.population_size
    njt = master_config.NJT

    log.info(f"Using {njt} DoF based on PlantConfig.")
    log.info("Input data (trajectory, motor_commands) generated.", dof=njt)

    res = master_config.simulation.resolution
    time_span_per_trial = master_config.simulation.duration_single_trial_ms
    total_sim_duration = master_config.simulation.total_duration_all_trials_ms

    total_time_vect_concat = np.linspace(
        0,
        total_sim_duration,
        num=int(np.round(total_sim_duration / res)),
        endpoint=True,
    )

    log.debug(
        "Time vectors calculated",
        total_duration=total_sim_duration,
        single_trial_duration=time_span_per_trial,
        num_steps_total=len(total_time_vect_concat),
    )

    controllers = []
    log.info(f"Constructing Network", dof=njt, N_neurons_pop=N)
    for j in range(njt):
        log.info(f"Creating controller", dof=j)

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
            path_data=master_config.run_paths.data_nest,  # TOCHECK: path_data from master_config
            label_prefix="",
            music_cfg=master_config.music,
            use_cerebellum=master_config.USE_CEREBELLUM,
            cerebellum_paths=master_config.bsb_config_paths,
        )
        controllers.append(controller)
    return controllers
