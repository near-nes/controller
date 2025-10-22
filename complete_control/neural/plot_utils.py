import json
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import structlog
from config.MasterParams import MasterParams
from config.paths import RunPaths
from mpi4py import MPI
from PIL import Image

from complete_control.neural.neural_models import SynapseBlock

from .neural_models import PopulationSpikes

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


def plot_rate(time_v, ts, pop_size, buffer_sz, ax, title="", normalize=False, **kwargs):
    """Computes and plots the smoothed PSTH for a set of spike times."""
    if ts.size == 0 or pop_size == 0:
        ax.plot([], [], **kwargs)  # Plot empty to keep colors consistent
        return 0

    time_end = time_v[-1] if len(time_v) > 0 else 0
    bins = np.arange(0, time_end + 1, buffer_sz)
    count, _ = np.histogram(ts, bins=bins)
    rate = 1000 * count / (pop_size * buffer_sz)

    # Smoothing
    rate_padded = np.pad(rate, pad_width=2, mode="reflect")
    rate_sm = np.convolve(rate_padded, np.ones(5) / 5, mode="valid")

    if normalize:
        rate_sm = rate_sm / np.max(rate_sm) if np.max(rate) > 0 else rate

    ax.plot(bins[:-1], rate_sm, **kwargs)
    if title:
        ax.set_ylabel(title, fontsize=15)
    ax.set_xlabel("Time [ms]")

    if normalize:
        ax.set_ylim(0, 1)

    # add return for keep max_value to scale the plot (if rate_sm is not empty)
    if rate_sm.size > 0:
        ymax = np.max(rate_sm)
        return ymax
    else:
        return 0


def global_to_local_ids(x: PopulationSpikes, hist_logscale=False):
    old2newid = {oldid: i for i, oldid in enumerate(x.gids)}
    return np.array([old2newid[i] for i in x.senders])


def generate_plot_fig(
    time_v,
    pop_p_data,
    pop_n_data,
    title,
    buffer_size,
    ts_p,
    ts_n,
    y_p,
    y_n,
):
    fig = plt.figure(figsize=(10, 6))
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 3, 1, 5], hspace=0.065)
    ax = [None] * 3
    ax[0] = fig.add_subplot(gs[0])
    ax[1] = fig.add_subplot(gs[1])
    ax[2] = fig.add_subplot(gs[3])

    # Raster plot
    ax[0].scatter(ts_p, y_p, marker=".", s=1, c="r", label="Positive")
    ax[0].set_title(title, fontsize=16)
    ax[0].set_ylim(bottom=-1, top=pop_p_data.population_size + 1)
    ax[0].set_xticklabels([])
    ax[0].legend(fontsize=16, loc="lower right")

    ax[1].scatter(ts_n, y_n, marker=".", s=1, c="b", label="Negative")
    ax[1].set_ylim(bottom=-(pop_n_data.population_size + 1), top=1)
    ax[1].legend(fontsize=16, loc="upper right")

    fig.text(0.045, 0.7, "Raster", va="center", rotation="vertical", fontsize=15)

    # Configure spines and subplot labels for both plots
    cnt_ax = 0
    for i, axs in enumerate(ax):
        axs.spines["top"].set_visible(False)
        axs.spines["right"].set_visible(False)
        axs.spines["bottom"].set_visible(True)
        axs.spines["left"].set_visible(True)
        # Add subplot labels (A, B), skip 2nd raster (y_n)
        if i != 1:
            axs.text(
                -0.1,
                1.1,
                chr(65 + cnt_ax),  # ASCII 65 is 'A'
                transform=axs.transAxes,
                fontsize=16,
                fontweight="bold",
                va="top",
                ha="right",
            )
            cnt_ax += 1
        axs.grid(True, which="both", linestyle="--", linewidth=0.5)

    # set specific spines
    ax[0].spines["bottom"].set_visible(False)
    ax[0].tick_params(axis="x", which="both", length=0)

    # Plotting rates
    max_p = plot_rate(
        time_v,
        ts_p,
        pop_p_data.population_size,
        buffer_size,
        ax=ax[2],
        color="r",
        label="Positive",
        normalize=False,
    )
    max_n = plot_rate(
        time_v,
        ts_n,
        pop_n_data.population_size,
        buffer_size,
        ax=ax[2],
        color="b",
        title="PSTH (Hz)",
        label="Negative",
        normalize=False,
    )
    ax[2].legend(fontsize=16)

    # scale PSTH plot
    max_y = max(max_p, max_n)
    ax[2].set_ylim(bottom=0, top=max_y + 1)

    # Align plot on x-axis
    time_end = time_v[-1] if len(time_v) > 0 else 0
    for i, axs in enumerate(ax):
        axs.set_xlim(left=0, right=time_end)
    ax[1].tick_params(labelbottom=True)
    ax[2].tick_params(labelbottom=True)

    return fig, ax


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

    fig, ax = generate_plot_fig(
        time_v,
        pop_p_data,
        pop_n_data,
        title,
        buffer_size,
        ts_p,
        ts_n,
        y_p,
        y_n,
    )

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
    ax[0].tick_params(labelbottom=True)

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

    max_y = plot_rate(
        time_v,
        pop_data.times,
        pop_data.population_size,
        buffer_size,
        ax=ax[1],
        color="r",
        title="PSTH (Hz)",
        normalize=False,
    )
    ax[1].set_ylim(bottom=0, top=max_y + 1)
    fig.tight_layout()

    if filepath:
        fig.savefig(filepath)
        _log.debug(f"Saved plot at {filepath}")
        plt.close(fig)

    return fig, ax


def plot_population_trial(
    nt,
    time_s,
    time_trial,
    pop_p_path: Path,
    pop_n_path: Path,
    title="",
    buffer_size=15,
):
    """Plots raster and PSTH for a population pair from data files."""
    pop_p_data = load_spike_data_from_file(pop_p_path)
    pop_n_data = load_spike_data_from_file(pop_n_path)

    t0 = nt * time_trial
    t1 = (nt + 1) * time_trial

    mask_p = (pop_p_data.times >= t0) & (pop_p_data.times < t1)
    mask_n = (pop_n_data.times >= t0) & (pop_n_data.times < t1)

    ts_p = pop_p_data.times[mask_p] - t0
    ts_n = pop_n_data.times[mask_n] - t0

    y_p = global_to_local_ids(pop_p_data)[mask_p]
    y_n = -global_to_local_ids(pop_n_data)[mask_n]

    fig, ax = generate_plot_fig(
        time_s,
        pop_p_data,
        pop_n_data,
        title,
        buffer_size,
        ts_p,
        ts_n,
        y_p,
        y_n,
    )

    return fig, ax


def handle_trial(
    trials2plot,
    lgd,
    i,
    populations_to_plot_trial,
    path_data,
    single_trial_time_vect_concat,
    single_trial_duration,
    path_fig="",
):
    all_trials_imgs = []
    for nt in trials2plot:
        trial_imgs = {}

        for file_prefix in populations_to_plot_trial:
            plot_name_t = file_prefix
            _log.debug(f"Plotting trial {nt} for {plot_name_t}...")

            pop_p_path_t = path_data / f"{file_prefix}_p.json"
            pop_n_path_t = path_data / f"{file_prefix}_n.json"

            fig_ipop, ax_ipop = plot_population_trial(
                nt,
                single_trial_time_vect_concat,
                single_trial_duration,
                pop_p_path_t,
                pop_n_path_t,
                title=f"{plot_name_t.replace('_', ' ').title()} {lgd} Trial {nt}",
                buffer_size=15,
            )

            if path_fig:
                trial_plot_path = path_fig / "Trials" / f"{plot_name_t}_{i}"
                trial_plot_path.mkdir(parents=True, exist_ok=True)
                fig_ipop.savefig(
                    trial_plot_path / f"Trial_{nt}_{plot_name_t}_{i}.{FIGURE_EXT}"
                )
                _log.debug(
                    f"Saved plot at {trial_plot_path} / Trial_{nt}_{plot_name_t}_{i}.{FIGURE_EXT}"
                )
                plt.close(fig_ipop)

                # save img (no fig) for collage
                trial_img = Image.open(
                    trial_plot_path / f"Trial_{nt}_{plot_name_t}_{i}.{FIGURE_EXT}"
                )
                trial_imgs[plot_name_t] = trial_img

        all_trials_imgs.append(trial_imgs)

    return all_trials_imgs


def create_collage(
    all_trials_imgs,
    pop_collage,
    path_fig,
):
    _log.debug(f"Generating per trial collage for {pop_collage} populations...")

    width, height = all_trials_imgs[0][pop_collage[0]].size
    collage = Image.new(
        "RGB",
        (width, height * len(pop_collage)),
        color=(255, 255, 255),
    )

    for nt, trial_dict in enumerate(all_trials_imgs):
        cnt_p = 0
        for pop, img in trial_dict.items():
            if pop in pop_collage:
                collage.paste(img, (0, height * cnt_p))
                cnt_p += 1

        if path_fig:
            collage_path = path_fig / "Collage"
            collage_path.mkdir(parents=True, exist_ok=True)
            collage.save(collage_path / f"Trial_{nt}_collage.{FIGURE_EXT}")
            _log.debug(f"Saved plot at {collage_path}")

    return


def plot_overlay(
    trials2plot,
    populations_to_overlay: list,
    path_data,
    single_trial_time_vect_concat,
    time_trial,
    path_fig,
    normalize=False,
):

    for nt in trials2plot:
        fig_overl, ax_overl = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        _log.debug(f"Generating overlayed plot for trial {nt}...")

        for file_prefix in populations_to_overlay:
            plot_name_t = file_prefix

            pop_p_path = path_data / f"{file_prefix}_p.json"
            pop_n_path = path_data / f"{file_prefix}_n.json"

            pop_p_data = load_spike_data_from_file(pop_p_path)
            pop_n_data = load_spike_data_from_file(pop_n_path)

            t0 = nt * time_trial
            t1 = (nt + 1) * time_trial

            mask_p = (pop_p_data.times >= t0) & (pop_p_data.times < t1)
            mask_n = (pop_n_data.times >= t0) & (pop_n_data.times < t1)

            ts_p = pop_p_data.times[mask_p] - t0
            ts_n = pop_n_data.times[mask_n] - t0

            plot_rate(
                single_trial_time_vect_concat,
                ts_p,
                pop_p_data.population_size,
                buffer_sz=15,
                ax=ax_overl[0],
                label=f"{plot_name_t}_p",
                normalize=normalize,
            )

            plot_rate(
                single_trial_time_vect_concat,
                ts_n,
                pop_n_data.population_size,
                buffer_sz=15,
                ax=ax_overl[1],
                label=f"{plot_name_t}_p",
                normalize=normalize,
            )

        for ax in ax_overl:
            ax.legend(fontsize=8)
            if normalize:
                ax.set_ylabel("Normalized rate")
            else:
                ax.set_ylabel("Rate (Hz)")

        ax_overl[0].set_title("Overlayed positive populations (PSTH)")
        ax_overl[1].set_title("Overlayed negative populations (PSTH)")

        fig_overl.tight_layout()

        if path_fig:
            overl_path = path_fig / "Overlayed plots"
            if normalize:
                overl_path = overl_path / "Normalized"
            overl_path.mkdir(parents=True, exist_ok=True)

            if normalize:
                fig_overl.savefig(overl_path / f"Trial_{nt}_normalized.{FIGURE_EXT}")
            else:
                fig_overl.savefig(overl_path / f"Trial_{nt}.{FIGURE_EXT}")
            _log.debug(
                f"Saved overlayed plot at {overl_path} / Trial_{nt}.{FIGURE_EXT}"
            )
            plt.close(fig_overl)
    return


def plot_controller_outputs(run_paths: RunPaths):
    """Plots outputs for various populations from a simulation run directory. Both entire simulation and per trial plots"""

    if MPI.COMM_WORLD.rank != 0:
        return  # Only rank 0 plots

    with open(run_paths.params_json) as f:
        master_config = MasterParams.model_validate_json(f.read())

    path_fig = run_paths.figures
    path_data = run_paths.data_nest

    path_fig.mkdir(parents=True, exist_ok=True)

    res = master_config.simulation.resolution
    total_sim_duration = master_config.simulation.total_duration_all_trials_ms
    total_time_vect_concat = np.linspace(
        0,
        total_sim_duration,
        num=int(np.round(total_sim_duration / res)),
        endpoint=True,
    )
    single_trial_duration = master_config.simulation.duration_single_trial_ms
    single_trial_time_vect_concat = np.linspace(
        0,
        single_trial_duration,
        num=int(np.round(single_trial_duration / res)),
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
        "mc_m1",
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

    # PLOT PER TRIALS
    populations_to_plot_trial = [
        "planner",
        "brainstem",
        "mc_out",
        "mc_m1",
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

    populations_to_collage = [
        "planner",
        "sensoryneur",
        # "cereb_core_forw_dcnp",
        # "cereb_core_forw_io",
        # "cereb_core_forw_pc",
        "cereb_feedback",
        "cereb_error",
        "pred",
        "state",
    ]

    populations_to_overlay = [
        "planner",
        # "sensoryneur",
        # "cereb_core_forw_dcnp",
        # "cereb_core_forw_io",
        # "cereb_core_forw_pc",
        "cereb_feedback",
        # "cereb_error",
        "pred",
        "state",
    ]

    # Set trials to plot
    trials2plot = "all"  # [1,15,30]
    if trials2plot == "all":
        trials2plot = list(range(master_config.simulation.n_trials))

    trials_imgs = handle_trial(
        trials2plot,
        lgd,
        i,
        populations_to_plot_trial,
        path_data,
        single_trial_time_vect_concat,
        single_trial_duration,
        path_fig,
    )

    create_collage(
        trials_imgs,
        populations_to_collage,
        path_fig,
    )

    # plot both normalized and not normalized overlayed plots
    plot_overlay(
        trials2plot,
        populations_to_overlay,
        path_data,
        single_trial_time_vect_concat,
        single_trial_duration,
        path_fig,
        normalize=True,
    )

    plot_overlay(
        trials2plot,
        populations_to_overlay,
        path_data,
        single_trial_time_vect_concat,
        single_trial_duration,
        path_fig,
        normalize=False,
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
