import argparse
import os
import sys
from pathlib import Path

import structlog

# Ensure we can import from the current directory
sys.path.append(str(Path(__file__).parent.resolve()))

from nrp_start_sim import run_trial as run_trial_nrp_func

log = structlog.get_logger()


def run_trial_nrp(trial_num: int, total_trials: int, parent_id: str, label: str) -> str:
    """Runs a single NRP simulation trial using direct Python call."""
    log.info(f"--- Starting NRP Trial {trial_num}/{total_trials} ---")

    if not run_trial_nrp_func:
        raise ImportError(
            "Could not import run_trial from nrp_start_sim. Is the file present?"
        )

    if parent_id:
        log.info(f"Continuing from parent run: {parent_id}")
    else:
        log.info("Starting a new simulation chain.")

    try:
        run_id = run_trial_nrp_func(parent_id=parent_id, label=label)
        log.info(f"Trial {trial_num} completed successfully. Run ID: {run_id}")
        return run_id
    except Exception as e:
        log.error("NRP Simulation trial failed.", exc_info=True)
        raise RuntimeError("Simulation failed") from e


def main():
    parser = argparse.ArgumentParser(description="Run a series of chained simulations.")
    parser.add_argument(
        "num_trials",
        type=int,
        help="The number of trials to run sequentially.",
    )
    parser.add_argument(
        "--parent-id",
        type=str,
        help="Optional starting parent ID. If not provided, starts a fresh chain.",
        default=None,
    )
    parser.add_argument(
        "--label",
        type=str,
        help="The simulation backend to use (default: '').",
        default="",
    )
    args = parser.parse_args()

    if args.num_trials <= 0:
        log.error("Number of trials must be a positive integer.")
        sys.exit(1)

    current_parent_id = args.parent_id or ""

    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)
    log.info(f"Working directory: {os.getcwd()}")
    log.info(f"Starting NRP simulation series of {args.num_trials} trials.")

    for i in range(args.num_trials):
        try:
            run_id = run_trial_nrp(
                i + 1, args.num_trials, current_parent_id, args.label
            )

            current_parent_id = run_id
        except RuntimeError:
            log.error("Aborting simulation chain due to error.")
            sys.exit(1)
        except KeyboardInterrupt:
            log.warning("Simulation chain interrupted by user.")
            sys.exit(130)

    log.info("All trials completed successfully.")


if __name__ == "__main__":
    main()
