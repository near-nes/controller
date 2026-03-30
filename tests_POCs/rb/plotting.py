import numpy as np
import matplotlib.pyplot as plt


def plotPopulation_sd(
    time_v,
    N,
    firstID_p,
    firstID_n,
    pos_ts,
    pos_sds,
    neg_ts,
    neg_sds,
    reference,
    time_vecs,
    legend,
    styles,
    title="",
    buffer_size=15,
):
    y_p = pos_sds - firstID_p + 1
    y_n = -(neg_sds - firstID_n + 1)
    if not reference:
        fig, ax = plt.subplots(2, 1, sharex=True)
        ax[0].scatter(pos_ts, y_p, marker=".", s=1, c="r", label="pos")
        ax[0].scatter(neg_ts, y_n, marker=".", s=1, c="b", label="neg")
        ax[0].legend()
        ax[0].set_ylabel("raster")
        rate_p = plot_rate_sd(
            time_v, N, pos_ts, pos_sds, buffer_size, ax=ax[1], color="r"
        )
        rate_n = plot_rate_sd(
            time_v,
            N,
            neg_ts,
            neg_sds,
            buffer_size,
            ax=ax[1],
            color="b",
            title="PSTH (Hz)",
        )
        # ax[0].set_title(title)
        ax[0].set_ylim(bottom=-(N + 1), top=N + 1)

    else:
        fig, ax = plt.subplots(3, 1, sharex=True)
        for i, signal in enumerate(reference):
            ax[0].plot(time_vecs[i], signal, styles[i], label=legend[i])
            ax[0].legend()
            ax[0].set_ylabel("input (Hz)")
            # ax[0].axhline(y=0, color='k', linestyle='--')
        ax[1].scatter(pos_ts, y_p, marker=".", s=1, c="r", label="pos")
        ax[1].scatter(neg_ts, y_n, marker=".", s=1, color="b", label="neg")
        ax[1].set_ylabel("raster")
        ax[1].set_ylim(bottom=-(N + 1), top=N + 1)
        rate_p = plot_rate_sd(
            time_v, N, pos_ts, pos_sds, buffer_size, ax=ax[2], color="r", label="pos"
        )
        rate_n = plot_rate_sd(
            time_v,
            N,
            neg_ts,
            neg_sds,
            buffer_size,
            ax=ax[2],
            color="b",
            title="PSTH (Hz)",
            label="neg",
        )
        # ax[1].set_title(title)

    subplot_labels = ["A", "B", "C"]
    for i, axs in enumerate(ax):
        axs.text(
            -0.1,
            1.1,
            subplot_labels[i],
            transform=axs.transAxes,
            fontsize=16,
            fontweight="bold",
            va="top",
            ha="right",
        )
        ax[i].spines["top"].set_visible(False)
        ax[i].spines["right"].set_visible(False)
        ax[i].spines["bottom"].set_visible(True)
        ax[i].spines["left"].set_visible(True)

    return fig, ax, rate_p, rate_n


def plot_rate_sd(
    time, N, times, senders, buffer_sz=10, title="", ax=None, bar=True, **kwargs
):
    t_init = time[0]
    t_end = time[-1]

    bins, count, rate = computePSTH_sd(time, N, times, buffer_sz)
    # print(len(rate))
    rate_padded = np.pad(rate, pad_width=2, mode="reflect")
    rate_sm = np.convolve(rate_padded, np.ones(5) / 5, mode="valid")

    no_ax = ax is None
    if no_ax:
        fig, ax = plt.subplots(1)

    if bar:
        ax.bar(bins[:-1], rate, width=bins[1] - bins[0], **kwargs)
        ax.plot(bins[:-1], rate_sm, color="k")
    else:
        ax.plot(bins[:-1], rate_sm, **kwargs)
    ax.set(xlim=(t_init, t_end))
    ax.set_ylabel(title)
    ax.set_xlabel("Time [ms]")

    return rate


def computePSTH_sd(time, N, times, buffer_sz=10):
    t_init = time[0]
    t_end = time[-1]
    # print(np.shape(times))
    count, bins = np.histogram(times, bins=np.arange(t_init, t_end + 1, buffer_sz))
    rate = 1000 * count / (N * buffer_sz)
    return bins, count, rate
