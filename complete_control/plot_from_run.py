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


def parse_slice_notation(slice_str: str) -> slice:
    parts = slice_str.split(":")
    if len(parts) > 3:
        raise ValueError(
            f"Invalid slice notation '{slice_str}'. "
            "Expected format: [start]:[stop]:[step]"
        )
    parts += [None] * (3 - len(parts))
    start = int(parts[0]) if parts[0] and parts[0].strip() else None
    stop = int(parts[1]) if parts[1] and parts[1].strip() else None
    step = int(parts[2]) if parts[2] and parts[2].strip() else None
    return slice(start, stop, step)


def parse_selection(selection_str: str, total_length: int) -> list[int]:
    indices = []
    for part in selection_str.split(','):
        part = part.strip()
        if ':' in part:
            slice_obj = parse_slice_notation(part)
            indices.extend(range(total_length)[slice_obj])
        else:
            idx = int(part)
            if idx < 0:
                idx = total_length + idx
            indices.append(idx)
    return sorted(set(indices))


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
    parser.add_argument(
        "--select",
        type=str,
        default=None,
        help="Trial selection with indices and/or slices (e.g., '-5:' for last 5, '0,5,10' for specific trials, '1:5,10:20:2' for mixed)",
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
    log.info(f"{len(metas)} metas (trials) found!", parent_ids=[m.id for m in metas])

    if args.select:
        selected_indices = parse_selection(args.select, len(metas))
        original_count = len(metas)
        metas = [metas[i] for i in selected_indices]
        log.info(
            "Filtered trials using selection.",
            selection=args.select,
            selected_count=len(metas),
            total_count=original_count,
        )

    if not metas:
        log.error("No trials selected for plotting.")
        sys.exit(1)

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
