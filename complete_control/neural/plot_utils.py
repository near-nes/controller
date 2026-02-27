import json
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import structlog
from config.ResultMeta import ResultMeta
from matplotlib.axis import Axis
from matplotlib.figure import Figure
from mpi4py import MPI
from neural.neural_models import SynapseBlock
from PIL import Image, ImageDraw

from complete_control.config.MasterParams import MasterParams
from complete_control.utils_common.results import concatenate_neural_results

from .neural_models import PopulationSpikes
from .population_utils import POPS, POPS_PAIRED, POPS_SINGLE, POPS_TREE

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
    pop_p_data: PopulationSpikes,
    pop_n_data: PopulationSpikes,
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


def plot_population_paired(
    time_v,
    pop_p_data: PopulationSpikes | Path,
    pop_n_data: PopulationSpikes | Path,
    t0=0,
    t1=None,
    title="",
    buffer_size=15,
):
    """Plots raster and PSTH for a population pair from data files."""
    if isinstance(pop_p_data, Path) and isinstance(pop_n_data, Path):
        pop_p_data = load_spike_data_from_file(pop_p_data)
        pop_n_data = load_spike_data_from_file(pop_n_data)

    if t1 is None:
        t1 = time_v[-1]

    mask_p = (pop_p_data.times >= t0) & (pop_p_data.times < t1)
    mask_n = (pop_n_data.times >= t0) & (pop_n_data.times < t1)

    ts_p = pop_p_data.times[mask_p] - t0
    ts_n = pop_n_data.times[mask_n] - t0

    y_p = global_to_local_ids(pop_p_data)[mask_p]
    y_n = -global_to_local_ids(pop_n_data)[mask_n]

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

    return fig, ax


def plot_population_single(
    time_v,
    pop_data: Path | PopulationSpikes,
    title="",
    buffer_size=15,
    filepath=None,
):
    """Plots raster and PSTH for a population pair from data files."""
    if isinstance(pop_data, Path):
        pop_data = load_spike_data_from_file(pop_data)

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

    return fig, ax, filepath


def list_depth(lst):
    if isinstance(lst, list):
        return 1 + max((list_depth(i) for i in lst), default=0)
    return 0


def plot_populations_per_trial(
    trials2plot,
    lgd,
    i,
    populations_to_plot_trial,
    single_trial_time_vect_concat,
    single_trial_duration,
    path_fig="",
):

    all_trials_imgs = {}

    pop_list_depth = list_depth(populations_to_plot_trial)

    if pop_list_depth != 1 and pop_list_depth != 2:
        raise ValueError(
            f"The depth of the population_to_plot_trial list is {pop_list_depth}. Must be 1 or 2! "
        )
    elif pop_list_depth == 2 and len(populations_to_plot_trial) != len(trials2plot):
        raise ValueError(
            f"populations_to_plot_trial has {len(populations_to_plot_trial)} elements, but trials2plot has {len(trials2plot)}."
        )

    for tidx, nt in enumerate(trials2plot):
        trial_imgs = {}

        if pop_list_depth == 1:
            pops_to_plot = populations_to_plot_trial
        elif pop_list_depth == 2:
            pops_to_plot = populations_to_plot_trial[tidx]

        for pop_p_t, pop_n_t in pops_to_plot:
            plot_name_t = pop_p_t
            _log.debug(f"Plotting trial {nt} for {plot_name_t}...")

            tstart_trial = nt * single_trial_duration
            tend_trial = (nt + 1) * single_trial_duration

            fig_ipop, ax_ipop = plot_population_paired(
                single_trial_time_vect_concat,
                pop_p_t,
                pop_n_t,
                tstart_trial,
                tend_trial,
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

        all_trials_imgs[nt] = trial_imgs

    return all_trials_imgs


def create_collage(
    plotted: dict[object, tuple[Figure, Axis, Path]],
    path_fig: Path,
    label: str = "",
    paired: bool = False,
):

    first_img = Image.open(list(plotted.values())[0][2])

    width, height = first_img.size
    collage = Image.new(
        "RGB",
        (width, height * len(plotted)),
        color=(255, 255, 255),
    )
    draw = ImageDraw.Draw(collage)

    for i, (pop, (f, a, filepath)) in enumerate(plotted.items()):
        # if pop in trial_dict:
        img = Image.open(filepath)
        collage.paste(img, (0, height * i))
        # else:
        #     draw.rectangle(
        #         [(0, height * i), (width, height * (i + 1))],
        #         fill=(230, 230, 230),
        #         outline=(150, 150, 150),
        #     )
        #     text = f"{pop}: Plot not generated"
        #     draw.text(
        #         (width // 2 - 20, height * i + height // 2 - 20),
        #         text,
        #         fill=(0, 0, 0),
        #     )

    if path_fig:
        collage_path = path_fig / "Collage"
        collage_path.mkdir(parents=True, exist_ok=True)
        img_path = collage_path / f"{label}_collage.{FIGURE_EXT}"
        collage.save(img_path)
        _log.debug(f"Saved plot at {img_path}")

    return


def extract_neural_and_merge(metas: list[ResultMeta]):
    neural_concat = concatenate_neural_results(metas)
    ref_mc: MasterParams = metas[0].load_params()

    total_sim_duration = sum(
        p.simulation.duration_ms for p in [m.load_params() for m in metas]
    )
    time_vect = np.linspace(
        0,
        total_sim_duration,
        num=int(np.round(total_sim_duration / ref_mc.simulation.resolution)),
        endpoint=True,
    )
    return neural_concat, ref_mc, time_vect


def plot_overlay(
    metas,
    populations_to_overlay: list[str],
    path_fig,
    normalize=True,
    label="",
):

    fig_overl, ax = plt.subplots(1, 1, figsize=(10, 6), sharex=True)

    neural_concat, ref_mc, time_vect = extract_neural_and_merge(metas)

    for file_prefix in populations_to_overlay:
        plot_name_t = file_prefix

        pop_data = neural_concat.get_pop(file_prefix)

        plot_rate(
            time_vect,
            pop_data.times,
            pop_data.population_size,
            buffer_sz=15,
            ax=ax,
            label=plot_name_t,
            normalize=normalize,
        )

    ax.legend(fontsize=8)
    ax.set_ylabel("Normalized rate" if normalize else "Rate (Hz)")
    ax.set_title("Overlayed populations (PSTH)")

    fig_overl.tight_layout()

    if path_fig:
        overl_path = path_fig / f"overlayed/{'normalized' if normalize else ''}"
        overl_path.mkdir(parents=True, exist_ok=True)
        save_path = (
            overl_path / f"{label}_{'normalized' if normalize else ''}.{FIGURE_EXT}"
        )
        fig_overl.savefig(save_path)
        _log.debug(f"Saved overlayed plot at {save_path}")
        plt.close(fig_overl)
    return


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def merge_and_plot(
    metas: list[ResultMeta],
    pops_single=POPS_SINGLE,
    pops_paired=POPS_PAIRED,
    path_fig=None,
):
    neural_concat, ref_mc, time_vect = extract_neural_and_merge(metas)
    path_fig = path_fig or ref_mc.run_paths.figures

    plotted = {}
    for pair in pops_paired:
        fig_pop, ax_pop = plot_population_paired(
            time_vect,
            neural_concat.get_pop(pair[0]),
            neural_concat.get_pop(pair[1]),
            title=f"{pair[0].replace('_', ' ').title()}",
            buffer_size=15,
        )

        filepath = path_fig / f"{pair[0]}.{FIGURE_EXT}"
        if filepath:
            fig_pop.savefig(filepath)
            _log.debug(f"Saved plot at {filepath}")
            plt.close(fig_pop)
        plotted[pair] = (fig_pop, ax_pop, filepath)

    for pop in pops_single:
        plot_name = pop
        _log.debug(f"Plotting for {plot_name}...")

        filepath = path_fig / f"{plot_name}.{FIGURE_EXT}"
        fig, ax, filepath = plot_population_single(
            time_vect,
            neural_concat.get_pop(pop),
            title=f"{plot_name.replace('_', ' ').title()}",
            buffer_size=15,
            filepath=filepath,
        )
        plotted[pop] = (fig, ax, filepath)
    return plotted


def plot_controller_outputs(metas: list[ResultMeta]):
    """Plots outputs for various populations from a simulation run directory. Both entire simulation and per trial plots"""

    if MPI.COMM_WORLD.rank != 0:
        return  # Only rank 0 plots

    ref_mc = metas[0].load_params()
    ref_rp = ref_mc.run_paths

    path_fig = ref_rp.figures
    path_fig.mkdir(parents=True, exist_ok=True)

    pops_single_list = [POPS.forw_mf]
    pops_paired_list = [
        (POPS.planner_p, POPS.planner_n),
        (POPS.sn_p, POPS.sn_n),
    ]

    # merge_and_plot(metas)

    p = merge_and_plot(
        [metas[0]],
        # [metas[0], metas[-1]],
        pops_single=pops_single_list,
        pops_paired=pops_paired_list,
    )

    create_collage(p, path_fig, "first-last")

    populations_to_overlay = [
        POPS.state_p,
        POPS.planner_p,
        POPS.sensory_delayed_p,
        POPS.pred_p,
        POPS.pred_n,
    ]
    plot_overlay(
        [metas[0], metas[-1]],
        populations_to_overlay,
        path_fig,
        normalize=False,
        label="plan-feed-pred-state",
    )

    # for n in [m.load_neural() for m in metas]:
    #     for p in n.weights:
    #         plot_synaptic_weight_evolution(
    #             p,
    #             max_synapses=500,
    #             fig_path=ref_rp.figures / p,
    #         )

    _log.debug("Plot generation finished.")

    _log.debug("Plot generation finished.")
