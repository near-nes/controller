import datetime
import os
from timeit import default_timer as timer

import structlog
from config.MasterParams import MasterParams
from config.nrp_sim_config import SimulationConfig
from config.paths import RunPaths
from config.ResultMeta import ResultMeta, extract_id
from nrp_client import NrpCore
from plant.plant_plotting import plot_plant_outputs
from tqdm import tqdm
from utils_common.results import make_trial_id


def _dump_logs(run_paths: RunPaths):
    """Print all log files from the run directory to stderr for debugging."""
    log = structlog.get_logger("nrp_client")
    for logfile in sorted(run_paths.logs.glob("*.log")):
        try:
            log.error(f"--- {logfile.name} ---\n{logfile.read_text()}")
        except Exception:
            pass


def run_trial(parent_id: str = "", label: str = "") -> str:
    client_log = structlog.get_logger("nrp_client")

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
        log_output="nrpcore_log.log",
        args=f"--logdir {run_paths.logs}",
    )

    client_log.debug(f"Starting NRP, logs in {run_paths.logs / 'nrpcore_log.log'}")

    start_time = timer()

    try:
        nrp.initialize()
    except Exception:
        _dump_logs(run_paths)
        raise
    client_log.debug("Nrp server initialized successfully")

    loop_start_time = timer()
    steps = master_config.simulation.sim_steps
    client_log.info(f"Start run loop. 1 trial ({steps} total iterations)")

    try:
        it_step = max(15, int(steps / 100))
        with tqdm(
            total=steps,
            desc=f"Simulation",
            unit="iter",
            leave=False,
        ) as pbar_trial:

            for i in [min(it_step, steps - i) for i in range(0, steps, it_step)]:
                nrp.run_loop(i)
                pbar_trial.update(i)
    except Exception:
        _dump_logs(run_paths)
        raise

    loop_end_time = timer()
    total_loop_time = datetime.timedelta(seconds=loop_end_time - loop_start_time)
    client_log.debug(f"Simulation time: {total_loop_time.total_seconds():.1f} s")

    nrp.shutdown()

    result = ResultMeta.create(master_config)
    result.save(master_config.run_paths)

    if master_config.plotting.PLOT_AFTER_SIMULATE:
        client_log.info("--- Generating Plots (Standalone) ---")
        plot_start_time = timer()
        # plot_controller_outputs([result])
        plot_plant_outputs([result])
        # draw_schema([result])
        plot_end_time = timer()
        total_plot_time = datetime.timedelta(seconds=plot_end_time - plot_start_time)
        client_log.info(f"Plotting Finished. {total_plot_time.total_seconds():.1f} s")

    # recap logs
    end_time = timer()
    total_time = datetime.timedelta(seconds=end_time - start_time)
    client_log.info(
        f"Simulation completed. Total execution time: {total_time.total_seconds():.1f} s"
    )

    return run_id


def main():
    parent_id = extract_id(os.environ.get("PARENT_ID") or "")
    run_id = run_trial(parent_id)
    print(f"__SIMULATION_RUN_ID__:{run_id}", flush=True)


if __name__ == "__main__":
    main()
