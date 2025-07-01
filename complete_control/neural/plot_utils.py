from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import structlog
from config.MasterParams import MasterParams
from config.paths import RunPaths
from mpi4py import MPI

_log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


def load_spike_data_from_file(filepath: Path) -> tuple[np.ndarray, np.ndarray]:
    if not filepath.exists():
        _log.warning(
            "Spike data file not found, returning empty arrays.", path=str(filepath)
        )
        return np.array([]), np.array([])
    # Skip header by finding the first line not starting with #
    with open(filepath, "r") as f:
        first_line = 0
        for line in f:
            if line.startswith("#") or line.startswith("s"):
                first_line += 1
            else:
                break
    try:
        df = pd.read_csv(filepath, sep="\t", header=0, skiprows=first_line)
    except pd.errors.EmptyDataError:
        _log.warning("empty results file", file=filepath)
        return np.array([]), np.array([])

    df.columns = ["sender", "time_ms"]
    senders = df["sender"].values
    times = df["time_ms"].values
    return senders, times


def plot_rate(time_v, ts, pop_size, buffer_sz, ax, title="", **kwargs):
    """Computes and plots the smoothed PSTH for a set of spike times."""
    if ts.size == 0 or pop_size == 0:
        ax.plot([], [], **kwargs)  # Plot empty to keep colors consistent
        return

    time_end = time_v[-1] if len(time_v) > 0 else 0
    bins = np.arange(0, time_end + 1, buffer_sz)
    count, _ = np.histogram(ts, bins=bins)
    rate = 1000 * count / (pop_size * buffer_sz)

    # Smoothing
    rate_padded = np.pad(rate, pad_width=2, mode="reflect")
    rate_sm = np.convolve(rate_padded, np.ones(5) / 5, mode="valid")

    ax.plot(bins[:-1], rate_sm, **kwargs)
    if title:
        ax.set_ylabel(title, fontsize=15)
    ax.set_xlabel("Time [ms]")
    ax.set_xlim(left=0, right=time_end)


def plot_population(
    time_v,
    pop_p_path: Path,
    pop_n_path: Path,
    pop_size: int,
    title="",
    buffer_size=15,
    filepath=None,
):
    """Plots raster and PSTH for a population pair from data files."""
    evs_p, ts_p = load_spike_data_from_file(pop_p_path)
    evs_n, ts_n = load_spike_data_from_file(pop_n_path)

    # Normalize sender GIDs to be relative to the population start
    # Get the base neuron ID by getting minimum ID for each population
    base_id_p = np.min(evs_p) if evs_p.size > 0 else 0
    base_id_n = np.min(evs_n) if evs_n.size > 0 else 0

    # Normalize IDs relative to the base ID for each population
    y_p = evs_p - base_id_p + 1 if evs_p.size > 0 else np.array([])
    y_n = -(evs_n - base_id_n + 1) if evs_n.size > 0 else np.array([])

    fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 6))

    # Raster plot
    ax[0].scatter(ts_p, y_p, marker=".", s=1, c="r", label="Positive")
    ax[0].scatter(ts_n, y_n, marker=".", s=1, c="b", label="Negative")
    ax[0].set_ylabel("raster", fontsize=15)
    ax[0].set_title(title, fontsize=16)
    ax[0].set_ylim(bottom=-(pop_size + 1), top=pop_size + 1)
    ax[0].legend(fontsize=16)

    # Configure spines and subplot labels for both plots
    for i, axs in enumerate(ax):
        axs.spines["top"].set_visible(False)
        axs.spines["right"].set_visible(False)
        axs.spines["bottom"].set_visible(True)
        axs.spines["left"].set_visible(True)
        # Add subplot labels (A, B)
        axs.text(
            -0.1,
            1.1,
            chr(65 + i),  # ASCII 65 is 'A'
            transform=axs.transAxes,
            fontsize=16,
            fontweight="bold",
            va="top",
            ha="right",
        )
        axs.grid(True, which="both", linestyle="--", linewidth=0.5)

    # Plotting rates
    plot_rate(
        time_v, ts_p, pop_size, buffer_size, ax=ax[1], color="r", label="Positive"
    )
    plot_rate(
        time_v,
        ts_n,
        pop_size,
        buffer_size,
        ax=ax[1],
        color="b",
        title="PSTH (Hz)",
        label="Negative",
    )
    ax[1].legend(fontsize=16)

    if filepath:
        fig.savefig(filepath)
        _log.debug(f"Saved plot at {filepath}")
        plt.close(fig)

    return fig, ax


def plot_population_single(
    time_v,
    pop_path: Path,
    pop_size: int,
    title="",
    buffer_size=15,
    filepath=None,
):
    """Plots raster and PSTH for a population pair from data files."""
    evs_p, ts_p = load_spike_data_from_file(pop_path)

    # Normalize sender GIDs to be relative to the population start
    # Get the base neuron ID by getting minimum ID for each population
    base_id_p = np.min(evs_p) if evs_p.size > 0 else 0
    y_p = evs_p - base_id_p + 1 if evs_p.size > 0 else np.array([])

    fig, ax = plt.subplots(1, 1, sharex=True, figsize=(10, 6))

    ax.scatter(ts_p, y_p, marker=".", s=1, c="r")
    ax.set_ylabel("raster", fontsize=15)
    ax.set_title(title, fontsize=16)
    ax.set_ylim(bottom=-(pop_size + 1), top=pop_size + 1)
    ax.legend(fontsize=16)
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)

    if filepath:
        fig.savefig(filepath)
        _log.debug(f"Saved plot at {filepath}")
        plt.close(fig)

    return fig, ax


def plot_controller_outputs(run_paths: RunPaths):
    """Plots outputs for various populations from a simulation run directory."""

    if MPI.COMM_WORLD.rank != 0:
        return  # Only rank 0 plots

    with open(run_paths.params_json) as f:
        master_config = MasterParams.model_validate_json(f.read())

    path_fig = run_paths.figures
    path_data = run_paths.data_nest

    path_fig.mkdir(parents=True, exist_ok=True)

    # Get parameters from config
    njt = master_config.NJT
    pop_size = master_config.brain.population_size
    res = master_config.simulation.resolution
    total_sim_duration = master_config.simulation.total_duration_all_trials_ms
    total_time_vect_concat = np.linspace(
        0,
        total_sim_duration,
        num=int(np.round(total_sim_duration / res)),
        endpoint=True,
    )

    _log.debug("Generating plots from run data...", run_dir=run_paths.run)

    # Assuming single DoF for now as requested
    i = 0
    lgd = f"DoF {i}"

    # Maps the final plot name to the prefix used for the .gdf data files
    populations_to_plot = {
        "planner": "planner",
        "brainstem": "brainstem",
        "mc_out": "mc_out",
        "state": "state",
        "sensoryneuron": "sensoryneur",
    }

    for plot_name, file_prefix in populations_to_plot.items():
        _log.debug(f"Plotting for {plot_name}...")

        pop_p_path = path_data / f"{file_prefix}_p.gdf"
        pop_n_path = path_data / f"{file_prefix}_n.gdf"

        plot_population(
            total_time_vect_concat,
            pop_p_path,
            pop_n_path,
            pop_size=pop_size,
            title=f"{plot_name.replace('_', ' ').title()} {lgd}",
            buffer_size=15,
            filepath=path_fig / f"{plot_name}_{i}.png",
        )
    populations_to_plot_single = {
        "motor_commands": "cereb_motor_commands",
        "plan_to_inv": "cereb_plan_to_inv",
        # "planner": "planner_p",
    }
    for plot_name, file_prefix in populations_to_plot_single.items():
        _log.debug(f"Plotting for {plot_name}...")

        pop_p_path = path_data / f"{file_prefix}.gdf"

        plot_population_single(
            total_time_vect_concat,
            pop_p_path,
            pop_size=pop_size,
            title=f"{plot_name.replace('_', ' ').title()} {lgd}",
            buffer_size=15,
            filepath=path_fig / f"{plot_name}_{i}.png",
        )

    _log.debug("Plot generation finished.")
