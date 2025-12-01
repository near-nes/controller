import datetime
import os
from timeit import default_timer as timer

import structlog
from config import ResultMeta
from config.MasterParams import MasterParams
from config.nrp_sim_config import SimulationConfig
from config.paths import RunPaths
from neural.plot_utils import plot_controller_outputs
from nrp_client import NrpCore
from nrp_protobuf import wrappers_pb2
from plant.plant_plotting import plot_plant_outputs
from tqdm import tqdm
from utils_common.results import make_trial_id


def run_trial(parent_id: str = "") -> str:
    client_log = structlog.get_logger("nrp_client")

    label = "singletrial"
    run_id = make_trial_id(label=label)

    os.environ["EXEC_TIMESTAMP"] = run_id
    if parent_id:
        os.environ["PARENT_ID"] = parent_id
    else:
        if "PARENT_ID" in os.environ:
            del os.environ["PARENT_ID"]

    # print(f"env['EXEC_TIMESTAMP']={os.environ.get('EXEC_TIMESTAMP')}")

    run_paths = RunPaths.from_run_id(run_id)
    master_config = MasterParams.from_runpaths(run_paths=run_paths, parent_id=parent_id)

    SimConfig = SimulationConfig.from_masterparams(master_config)

    simconfig_path = str(run_paths.params_json).replace(".json", "_simconfig.json")
    with open(simconfig_path, "w") as f:
        f.write(SimConfig.model_dump_json(indent=2))
    client_log.debug(
        f"SimulationConfig loaded and dumped successfully. in {simconfig_path}"
    )

    nrp = NrpCore(
        "0.0.0.0:5679",
        "/sim/controller/",
        simconfig_path,
        log_output=run_paths.logs / "nrpcore_log.log",
    )

    client_log.debug(f"Starting NRP, logs in {run_paths.logs / 'nrpcore_log.log'}")

    start_time = timer()

    nrp.initialize()
    client_log.debug("Nrp server initialized successfully")

    loop_start_time = timer()
    steps_trial = master_config.simulation.sim_steps
    client_log.info(f"Start run loop. 1 trial ({steps_trial} total iterations)")

    it_step = int(steps_trial / 100)
    with tqdm(
        total=steps_trial,
        desc=f"Simulation",
        unit="iter",
        leave=False,
    ) as pbar_trial:

        for i in range(int(steps_trial / it_step)):
            nrp.run_loop(it_step)
            pbar_trial.update(it_step)

    loop_end_time = timer()
    total_loop_time = datetime.timedelta(seconds=loop_end_time - loop_start_time)
    client_log.debug(f"Simulation time: {total_loop_time.total_seconds():.1f} s")

    nrp.shutdown()

    if master_config.plotting.PLOT_AFTER_SIMULATE:
        client_log.info("--- Generating Plots (Standalone) ---")
        plot_start_time = timer()
        plot_controller_outputs(run_paths)
        plot_plant_outputs(run_paths)
        plot_end_time = timer()
        total_plot_time = datetime.timedelta(seconds=plot_end_time - plot_start_time)
        client_log.info(f"Plotting Finished. {total_plot_time.total_seconds():.1f} s")

    # recap logs
    end_time = timer()
    total_time = datetime.timedelta(seconds=end_time - start_time)
    client_log.info(
        f"Simulation completed. Total execution time: {total_time.total_seconds():.1f} s"
    )

    result = ResultMeta.create(master_config)
    result.save(master_config.run_paths)

    return run_id


def main():
    # For standalone execution, we still support reading PARENT_ID from env
    # and printing the marker for the old runner if needed.
    parent_id = ResultMeta.extract_id(os.environ.get("PARENT_ID") or "")
    run_id = run_trial(parent_id)
    print(f"__SIMULATION_RUN_ID__:{run_id}", flush=True)


if __name__ == "__main__":
    main()
