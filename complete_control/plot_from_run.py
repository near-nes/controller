#!/usr/bin/env python3

import argparse
import dataclasses
import datetime
import sys
from pathlib import Path
import numpy as np
from complete_control.config import paths

# Add the project root to the Python path
# This is necessary to ensure that the script can find the `complete_control` package
# when run as a standalone script.
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))
import structlog

from complete_control.config.paths import RUNS_DIR, RunPaths
from complete_control.neural.plot_utils import plot_controller_outputs

from complete_control.plant.plant_plotting import plot_plant_outputs

log = structlog.get_logger()


def find_most_recent_run() -> Path | None:
    """Finds the most recent run directory in RUNS_DIR."""
    try:
        subdirs = [d for d in RUNS_DIR.iterdir() if d.is_dir()]
        if not subdirs:
            return None
        # Sort by name (which is the timestamp) to find the most recent
        latest_dir = max(subdirs, key=lambda d: d.name)
        return latest_dir
    except FileNotFoundError:
        return None


def main():
    """
    generates plots from existing simulation data.
    """
    parser = argparse.ArgumentParser(
        description="Generate plots from a completed simulation run directory. "
        "If no directory is provided, the most recent one is used."
    )
    parser.add_argument(
        "run_directory",
        type=str,
        nargs="?",
        default=None,
        help="The path to the simulation run directory (e.g., 'runs/20231027_120000'). "
        "If omitted, the latest run will be used.",
    )
    args = parser.parse_args()

    run_dir = None
    if args.run_directory:
        run_dir = Path(args.run_directory)
    else:
        log.info("No run directory provided, searching for the most recent one...")
        run_dir = find_most_recent_run()
        if not run_dir:
            log.error("No run directories found in RUNS_DIR.", path=str(RUNS_DIR))
            sys.exit(1)
        log.info("Found most recent run directory.", path=str(run_dir))

    if not run_dir.is_dir():
        log.error("The specified run directory does not exist.", path=str(run_dir))
        sys.exit(1)

    log.info("Setting up run paths...", run_directory=str(run_dir))

    # The timestamp is the name of the run directory
    current_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_timestamp_str = run_dir.name
    run_paths = RunPaths.from_run_id(run_timestamp_str)
    path_current_figures = (
        run_paths.run
        / f"manualplots@{current_timestamp}"
        / paths.FOLDER_NAME_NEURAL_FIGS
    )
    path_current_figures.mkdir(exist_ok=True, parents=True)
    path_current_receiver_figs = (
        run_paths.run
        / f"manualplots@{current_timestamp}"
        / paths.FOLDER_NAME_ROBOTIC_FIGS
    )
    path_current_receiver_figs.mkdir(exist_ok=True, parents=True)
    run_paths = dataclasses.replace(
        run_paths,
        figures=path_current_figures,
        figures_receiver=path_current_receiver_figs,
    )

    log.info("Generating plots...")
    plot_controller_outputs(run_paths)
    plot_plant_outputs(run_paths)

    log.info("Plotting complete.", output_directory=str(run_paths.figures))


if __name__ == "__main__":
    main()
