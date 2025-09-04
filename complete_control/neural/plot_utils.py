import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import structlog
from config.MasterParams import MasterParams
from config.paths import RunPaths
from mpi4py import MPI

from .neural_models import PopulationSpikes
from complete_control.neural.neural_models import SynapseBlock

_log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)
FIGURE_EXT = "png"


def load_spike_data_from_file(filepath: Path) -> PopulationSpikes:
    if not filepath.exists():
        _log.warning(
            "Spike data file not found, returning empty PopulationSpikes object.",
            path=str(filepath),
        )
        return PopulationSpikes(
            label=filepath.stem,
            gids=np.array([]),
            senders=np.array([]),
            times=np.array([]),
            population_size=0,
            neuron_model="unknown",
        )

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        return PopulationSpikes.model_validate(data)
    except Exception as e:
        _log.error(f"Error loading PopulationSpikes from {filepath}: {e}")
        raise


import matplotlib.pyplot as plt
import numpy as np
import logging


def plot_synaptic_weight_evolution(synapse_json_path, max_synapses=10, fig_path=None):
    """
    Plots the synaptic weight evolution for a SynapseBlock JSON file.
    Parameters:
        synapse_json_path (Path or str): Path to the synapse weight JSON file.
        max_synapses (int): Maximum number of synapses to plot.
        fig_path (Path or str): Path to save the figure.
    """
    with open(synapse_json_path, "r") as f:
        syn_block = SynapseBlock.model_validate_json(f.read())

    fig, ax = plt.subplots(1, 1, figsize=(15, 8))

    for i, rec in enumerate(syn_block.synapse_recordings):
        if rec.syn_type == "stdp_synapse_sinexp":
            if i >= max_synapses:
                break
            weights = np.array(rec.weight_history)
            ax.plot(range(len(weights)), weights, label=f"{rec.source}->{rec.target}")

    ax.set_xlabel("Trial")
    ax.set_ylabel("Synaptic weight")
    ax.set_title(
        f"Weight evolution: {syn_block.source_pop_label} → {syn_block.target_pop_label}"
    )

    ax.legend(fontsize="small")
    fig.tight_layout()
    if fig_path:
        fig.savefig(fig_path)


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
    ax.set_ylim(bottom=0)


def global_to_local_ids(x: PopulationSpikes, hist_logscale=False):
    old2newid = {oldid: i for i, oldid in enumerate(x.gids)}
    return np.array([old2newid[i] for i in x.senders])


def plot_population(
    time_v,
    pop_p_path: Path,
    pop_n_path: Path,
    title="",
    buffer_size=15,
    filepath=None,
):
    """Plots raster and PSTH for a population pair from data files."""
    pop_p_data = load_spike_data_from_file(pop_p_path)
    pop_n_data = load_spike_data_from_file(pop_n_path)

    ts_p = pop_p_data.times
    ts_n = pop_n_data.times

    y_p = global_to_local_ids(pop_p_data)
    y_n = -global_to_local_ids(pop_n_data)

    fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 6))

    # Raster plot
    ax[0].scatter(ts_p, y_p, marker=".", s=1, c="r", label="Positive")
    ax[0].scatter(ts_n, y_n, marker=".", s=1, c="b", label="Negative")
    ax[0].set_ylabel("raster", fontsize=15)
    ax[0].set_title(title, fontsize=16)
    ax[0].set_ylim(
        bottom=-(pop_n_data.population_size + 1), top=pop_p_data.population_size + 1
    )
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
        time_v,
        ts_p,
        pop_p_data.population_size,
        buffer_size,
        ax=ax[1],
        color="r",
        label="Positive",
    )
    plot_rate(
        time_v,
        ts_n,
        pop_n_data.population_size,
        buffer_size,
        ax=ax[1],
        color="b",
        title="PSTH (Hz)",
        label="Negative",
    )
    ax[1].legend(fontsize=16)
    fig.tight_layout()

    if filepath:
        fig.savefig(filepath)
        _log.debug(f"Saved plot at {filepath}")
        plt.close(fig)

    return fig, ax


def plot_population_single(
    time_v,
    pop_path: Path,
    title="",
    buffer_size=15,
    filepath=None,
):
    """Plots raster and PSTH for a population pair from data files."""
    pop_data = load_spike_data_from_file(pop_path)
    local_ids = global_to_local_ids(pop_data)

    fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 6))

    ax[0].scatter(pop_data.times, local_ids, marker=".", s=1, c="r")
    ax[0].set_ylabel("raster", fontsize=15)
    ax[0].set_title(title, fontsize=16)
    ax[0].set_ylim(bottom=0, top=pop_data.population_size + 1)

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

    plot_rate(
        time_v,
        pop_data.times,
        pop_data.population_size,
        buffer_size,
        ax=ax[1],
        color="r",
        title="PSTH (Hz)",
    )
    fig.tight_layout()

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
    # pop_size = master_config.brain.population_size # No longer needed, obtained from PopulationSpikes
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

    # Maps the final plot name to the prefix used for the .json data files
    populations_to_plot = [
        "planner",
        "brainstem",
        "mc_out",
        "mc_ffwd",
        "mc_fbk",
        "state",
        "sensoryneur",
        "cereb_core_forw_dcnp",
        "cereb_core_forw_io",
        "cereb_core_forw_pc",
        "cereb_core_inv_dcnp",
        "cereb_core_inv_io",
        "cereb_core_inv_pc",
        "cereb_error",
        "cereb_error_inv",
        "cereb_feedback",
        "cereb_feedback_inv",
        "cereb_motor_prediction",
        "cereb_state_to_inv",
        "fbk_smooth",
        "pred",
    ]

    for file_prefix in populations_to_plot:
        plot_name = file_prefix
        _log.debug(f"Plotting for {plot_name}...")

        pop_p_path = path_data / f"{file_prefix}_p.json"
        pop_n_path = path_data / f"{file_prefix}_n.json"

        plot_population(
            total_time_vect_concat,
            pop_p_path,
            pop_n_path,
            title=f"{plot_name.replace('_', ' ').title()} {lgd}",
            buffer_size=15,
            filepath=path_fig / f"{plot_name}_{i}.{FIGURE_EXT}",
        )

    populations_to_plot_single = [
        "cereb_motor_commands",
        "cereb_plan_to_inv",
        "cereb_core_forw_bc",
        "cereb_core_forw_glom",
        "cereb_core_forw_goc",
        "cereb_core_forw_grc",
        "cereb_core_forw_mf",
        "cereb_core_forw_sc",
        "cereb_core_inv_bc",
        "cereb_core_inv_glom",
        "cereb_core_inv_goc",
        "cereb_core_inv_grc",
        "cereb_core_inv_mf",
        "cereb_core_inv_sc",
    ]
    for file_prefix in populations_to_plot_single:
        plot_name = file_prefix
        _log.debug(f"Plotting for {plot_name}...")

        pop_p_path = path_data / f"{file_prefix}.json"

        plot_population_single(
            total_time_vect_concat,
            pop_p_path,
            title=f"{plot_name.replace('_', ' ').title()} {lgd}",
            buffer_size=15,
            filepath=path_fig / f"{plot_name}_{i}.{FIGURE_EXT}",
        )

    for json_file in sorted(run_paths.data_nest.glob("weightrecord*.json")):
        try:
            fig_filename = (
                json_file.stem.replace("weightrecord-", "") + "." + FIGURE_EXT
            )

            plot_synaptic_weight_evolution(
                json_file,
                max_synapses=500,
                fig_path=run_paths.figures / fig_filename,
            )
        except Exception as e:
            _log.warning(f"Failed to plot synaptic weights from {json_file}: {e}")

    _log.debug("Plot generation finished.")
