import argparse
import fcntl
import os
import pty
import re
import select
import shutil
import struct
import subprocess
import sys
import termios
from pathlib import Path

import structlog

# Ensure we can import from the current directory
sys.path.append(str(Path(__file__).parent.resolve()))

from nrp_start_sim import run_trial as run_trial_nrp_func

log = structlog.get_logger()


def run_trial_music(trial_num: int, total_trials: int, parent_id: str | None) -> str:
    """Runs a single MUSIC simulation trial using subprocess and pty."""
    log.info(f"--- Starting MUSIC Trial {trial_num}/{total_trials} ---")

    env = os.environ.copy()
    command = ["mpirun", "-np", "5", "music", "complete.music"]

    if parent_id:
        log.info(f"Continuing from parent run: {parent_id}")
        env["PARENT_ID"] = parent_id
    else:
        log.info("Starting a new simulation chain.")

    master_fd, slave_fd = pty.openpty()

    try:
        columns, lines = shutil.get_terminal_size(fallback=(80, 24))
        # struct winsize { unsigned short ws_row; unsigned short ws_col; unsigned short ws_xpixel; unsigned short ws_ypixel; };
        winsize = struct.pack("HHHH", lines, columns, 0, 0)
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)
    except Exception as e:
        log.warning(f"Could not set pty terminal size: {e}")

    try:
        process = subprocess.Popen(
            command,
            env=env,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
        )
        os.close(slave_fd)

        run_id = None
        output_buffer = b""

        while True:
            try:
                r, _, _ = select.select([master_fd], [], [], 0.1)
                if master_fd in r:
                    data = os.read(master_fd, 1024)
                    if not data:
                        break

                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()

                    if run_id is None:
                        output_buffer += data

                        if len(output_buffer) > 4096:
                            output_buffer = output_buffer[-256:]

                        match = re.search(
                            b"__SIMULATION_RUN_ID__:([a-zA-Z0-9_-]+)", output_buffer
                        )
                        if match:
                            run_id = match.group(1).decode("utf-8")
                            output_buffer = b""

            except OSError:
                break

            if process.poll() is not None:
                break

        return_code = process.wait()

        if return_code != 0:
            log.error(
                "Simulation trial failed.",
                return_code=return_code,
            )
            raise RuntimeError("Simulation failed")

        if not run_id:
            log.error("Simulation finished but Run ID marker not found in output.")
            raise RuntimeError("Run ID not found")

        log.info(f"Trial {trial_num} completed successfully. Run ID: {run_id}")
        return run_id

    except FileNotFoundError:
        log.error(
            f"Command not found: '{' '.join(command)}'. Is mpirun installed and in your PATH?"
        )
        raise RuntimeError("Command not found")
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass


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
        "--backend",
        type=str,
        choices=["music", "nrp"],
        default="nrp",
        help="The simulation backend to use (default: nrp).",
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
    log.info(
        f"Starting {args.backend.upper()} simulation series of {args.num_trials} trials."
    )

    for i in range(args.num_trials):
        try:
            if args.backend == "music":
                run_id = run_trial_music(i + 1, args.num_trials, current_parent_id)
            elif args.backend == "nrp":
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
