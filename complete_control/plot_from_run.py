#!/usr/bin/env python3

import argparse
import dataclasses
import datetime
import sys
from pathlib import Path

import structlog

from complete_control.config import paths
from complete_control.config.paths import RUNS_DIR, RunPaths
from complete_control.config.ResultMeta import ResultMeta
from complete_control.neural.plot_utils import plot_controller_outputs
from complete_control.plant.plant_plotting import plot_plant_outputs
from complete_control.utils_common.draw_schema import draw_schema
from complete_control.utils_common.results import gather_metas

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
        "id",
        type=str,
        nargs="?",
        default=None,
        help="ID to plot. If no ID is provided, the most recent one is used.",
    )
    args = parser.parse_args()

    metas = None
    run_dir = None

    if args.id:
        log.info("IDs provided, loading metas...", ids=args.id)
        metas = list(reversed(gather_metas(args.id)))
    else:
        log.info("No run directory provided, searching for the most recent one...")
        run_dir = find_most_recent_run()
        if not run_dir:
            log.error("No run directories found in RUNS_DIR.", path=str(RUNS_DIR))
            sys.exit(1)
        log.info("Found most recent run directory.", path=str(run_dir))
        metas = list(reversed(gather_metas(run_dir.name)))

    if run_dir and not run_dir.is_dir():
        log.error("The specified run directory does not exist.", path=str(run_dir))
        sys.exit(1)

    log.info("Generating plots...")
    # plot_controller_outputs(metas)
    plot_plant_outputs(metas)
    draw_schema(metas, scale_factor=0.005)

    log.info(
        "Plotting complete.",
        output_directory=str(RunPaths.from_run_id(metas[-1].id).figures),
    )


if __name__ == "__main__":
    main()
