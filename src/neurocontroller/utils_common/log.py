"""
Configures logging using structlog and standard logging.
MPI only!

Provides rank-aware logging with:
- Console output (rank 0 only, TQDM-friendly, colored/plain).
- Plain text file output (rank 0 only, mirrors console).
- JSONL file output (one file per rank).
- MPI rank information automatically added to log records.
- Filtering based on rank (configurable default, overridable per message).
- TQDM integration for progress bars that don't interfere with logging.
"""

import datetime
import logging
import os
import sys
from functools import partial
from pathlib import Path

import structlog
from mpi4py import MPI
from tqdm import tqdm as std_tqdm

rank = MPI.COMM_WORLD.rank
size = None

COLORS_IN_CONSOLE = True

# --- TQDM Configuration ---
# Make tqdm rank-aware (only display bar on rank 0)
tqdm = partial(std_tqdm, dynamic_ncols=True)
# tqdm = partial(std_tqdm, dynamic_ncols=True, disable=(rank != 0))


# --- TQDM Handler for standard logging ---
class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            std_tqdm.write(msg, file=sys.stderr)
            self.flush()
        except Exception:
            self.handleError(record)


# --- Structlog Custom Processors ---
def add_mpi_rank_processor(_, __, event_dict):
    """Adds MPI rank to the event dictionary."""
    event_dict["mpi_rank"] = rank
    return event_dict


# --- Logging Setup Function ---
def setup_logging(
    comm: MPI.Comm,
    log_dir_path: Path,
    timestamp_str: str,
    log_level="INFO",
    default_log_all_ranks=False,
):
    """
    Configures structlog for MPI application logging within a specified directory.

    Sets up console (rank 0 only, TQDM-friendly), plain text file (rank 0 only),
    and JSONL file handlers (one per rank).

    By default, only rank 0 logs are processed for console/plain file output,
    and only rank 0 logs pass the initial filter unless overridden.

    Args:
        comm: The MPI communicator.
        log_dir_path: The directory where log files will be created.
        timestamp_str: Start timestamp. Input so that it is the same across all usages
        log_level: The minimum logging level (e.g., "INFO", "DEBUG").
        default_log_all_ranks: If True, allows logs from all ranks by default,
                               unless overridden by `log_all_ranks=False` in a specific log call.
                               If False (default), only rank 0 logs pass the filter
                               unless overridden by `log_all_ranks=True`.
    """
    global rank, size  # Allow modification of global rank/size for the processor
    rank = comm.rank
    size = comm.size

    # --- Define Rank Filtering Processor ---
    # This processor controls which ranks' log messages are processed further.
    # It uses the 'default_log_all_ranks' and 'rank' variables from the outer scope.
    def _filter_by_rank_processor(logger, method_name, event_dict):
        """
        Drops events from ranks != 0 unless 'log_all_ranks' is explicitly True
        in the event dictionary or the default (default_log_all_ranks) is True.
        Removes 'log_all_ranks' field after checking.
        """
        # Check for per-message override, otherwise use the default captured from setup_logging
        log_all = event_dict.pop("log_all_ranks", default_log_all_ranks)
        # Use the 'rank' variable captured from the setup_logging scope
        if not log_all and rank != 0:
            raise structlog.DropEvent
        return event_dict

    # --- Shared Processors ---
    # Processors applied to all log records, regardless of destination
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=False),
        add_mpi_rank_processor,  # Add MPI rank info
        _filter_by_rank_processor,  # Filter based on rank (uses closure for default)
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,  # Prepare for stdlib formatters
    ]

    # --- Configure structlog ---
    structlog.configure(
        processors=shared_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Pass rank and default_log_all_ranks to the logger instance for the processor
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )

    # --- Setup Standard Library Handlers with structlog Formatters ---

    # 1. Console Handler (Human Readable, TQDM Friendly, Rank 0 Only)
    # only on rank 0 to avoid duplicate console output
    if rank == 0 or rank == size - 1:
        console_formatter = structlog.stdlib.ProcessorFormatter(
            # The final processor formats the log entry for console
            processor=structlog.dev.ConsoleRenderer(colors=COLORS_IN_CONSOLE),
        )
        console_handler = TqdmLoggingHandler()
        console_handler.setFormatter(console_formatter)

        # Get the root logger and add the handler
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)
        root_logger.setLevel(log_level.upper())  # Set level on the stdlib logger

        # 1.b. Plain Text File Handler (Mirrors Console, Rank 0 Only)
        log_file_plain_name = f"log_{timestamp_str}_console.log"
        log_file_plain_path = log_dir_path / log_file_plain_name
        plain_file_handler = logging.FileHandler(log_file_plain_path, mode="w")
        # Create a specific formatter for the plain file, disabling colors
        plain_file_formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=False),
        )
        plain_file_handler.setFormatter(plain_file_formatter)
        root_logger.addHandler(plain_file_handler)

    # 2. File Handler (JSONL, Rank-Specific File)
    # Each rank writes its own file.
    log_file_name = f"log_{timestamp_str}_rank{rank}.jsonl"
    log_file_path = log_dir_path / log_file_name

    file_handler = logging.FileHandler(log_file_path, mode="w")

    file_formatter = structlog.stdlib.ProcessorFormatter(
        # The final processor renders the log entry as JSON
        processor=structlog.processors.JSONRenderer(),
    )
    file_handler.setFormatter(file_formatter)

    # Add handler to the root logger (or a specific logger if preferred)
    root_logger = logging.getLogger()  # Get root logger again (safe)
    root_logger.addHandler(file_handler)
    # Ensure stdlib logger level is also set if adding handler here
    if rank != 0:  # Set level for other ranks if console handler wasn't added
        root_logger.setLevel(log_level.upper())

    # --- Suppress verbose matplotlib font manager logs ---
    # Set the level for the specific logger to WARNING or higher
    logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

    # --- Initial Log Message ---
    # Use get_logger() AFTER structlog.configure()
    log = structlog.get_logger("init")
    if rank == 0:
        log.info(
            "Logging configured",
            log_directory=str(log_dir_path),
            console_output=True,
            jsonl_output_pattern=f"{log_dir_path.name}/log_{timestamp_str}_rank<N>.jsonl",  # Use relative name for pattern clarity
            log_file_output=f"{log_dir_path.name}/log_{timestamp_str}_rank0.log",  # Use relative name for pattern clarity
        )
    # Barrier to ensure setup is complete everywhere before proceeding
    comm.Barrier()


# --- Example Usage ---
if __name__ == "__main__":

    # Configure logging level and base directory
    # Example: Enable all ranks by default
    # setup_logging(MPI.COMM_WORLD, log_level="DEBUG", default_log_all_ranks=True)
    # Example: Default behavior (only rank 0, INFO level)
    comm = MPI.COMM_WORLD
    example_log_dir = Path("./example_run_logs")
    if comm.rank == 0:
        example_log_dir.mkdir(parents=True, exist_ok=True)
    comm.Barrier()
    setup_logging(comm, log_dir_path=example_log_dir, log_level="DEBUG")

    # Get the logger for the main application part
    log: structlog.stdlib.BoundLogger = structlog.get_logger("simulation")

    # --- Basic Logging ---
    # This will only appear on console (rank 0) and in rank 0's file by default
    log.info("Application starting", mpi_size=size)
    log.info("START!", log_all_ranks=True)

    # This will only appear in rank 0's file by default
    log.debug("Debug message from rank 0 (should not appear unless level is DEBUG)")

    # --- Logging from a specific rank (if needed, usually for errors) ---
    if rank == 1:
        log.warning(
            "Special warning from rank 1", some_data=123, log_all_ranks=True
        )  # Appears in rank 1's file

    # --- Logging critical errors from all ranks ---
    # Example: Simulating an error condition detected by multiple ranks
    try:
        # Simulate something that might fail differently on ranks
        result = 10 / rank  # This will cause ZeroDivisionError on rank 0
    except Exception as e:
        log.error(
            "An error occurred during calculation",
            error=str(e),
            rank_value=rank,
            exc_info=True,
            log_all_ranks=True,
        )
        # log_all_ranks=True ensures this appears in the respective log file for *each* rank that fails.
        # exc_info=True adds traceback (works well with JSONRenderer)

    # Ensure all ranks reach this point before Rank 0 potentially exits
    comm.Barrier()

    # --- TQDM Integration Example ---
    if rank == 0:  # Only rank 0 controls the main loop progress bar typically
        log.info("Starting simulation loop...")

    num_steps = 10
    for i in tqdm(range(num_steps), desc="Simulation Progress"):
        for i in tqdm(range(5), desc="inner"):
            # Simulate work
            import time

            time.sleep(5)

            # Log something occasionally from rank 0 inside the loop
            if rank == 0 and i % 4 == 0:
                log.debug(
                    "Loop progress update", step=i, total_steps=num_steps
                )  # Only in rank 0 file

            # Simulate an infrequent event logged by another rank
            if rank == (size // 2) and i == num_steps // 2:
                # Use log_all_ranks=True if you want this specific event logged by this rank
                log.info(
                    "Midpoint event detected",
                    step=i,
                    detector_rank=rank,
                    log_all_ranks=True,
                )

    # Barrier before final message
    comm.Barrier()

    # Final message - only from Rank 0 by default
    log.info("Simulation loop finished.", log_all_ranks=True)

    # You might want a final barrier here depending on your MPI application structure
    comm.Barrier()
