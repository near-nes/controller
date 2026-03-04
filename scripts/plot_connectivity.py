"""!!! CAUTION !!! AI-generated, unreviewed code

Plot connectivity matrix from connectivity_debug.json.

Shows two views:
1. Raw connectivity ordered by GID
2. Reordered: plus neurons first, then minus, with separator lines

Both have claimed +/- labels overlaid so you can judge whether the split
actually matches the connectivity structure.
"""

import json
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


def _label_array(gids, plus_set, minus_set):
    """Assign a label to each GID: +1 = claimed plus, -1 = claimed minus, 0 = unlabelled."""
    labels = np.zeros(len(gids), dtype=int)
    for i, g in enumerate(gids):
        if g in plus_set:
            labels[i] = 1
        elif g in minus_set:
            labels[i] = -1
    return labels


def _draw_label_bar(ax, labels, orientation):
    """Draw a thin color bar next to an axis showing claimed +/- labels."""
    cmap = ListedColormap(["#4393c3", "#cccccc", "#d6604d"])  # minus, unlabelled, plus
    arr = (
        (labels + 1).reshape(1, -1)
        if orientation == "h"
        else (labels + 1).reshape(-1, 1)
    )
    if orientation == "h":
        extent = [-0.5, len(labels) - 0.5, 0, 1]
    else:
        extent = [0, 1, len(labels) - 0.5, -0.5]
    ax.imshow(
        arr,
        aspect="auto",
        cmap=cmap,
        vmin=0,
        vmax=2,
        interpolation="none",
        extent=extent,
    )
    ax.set_xticks([])
    ax.set_yticks([])


def _sort_by_label(gids, labels):
    """Return reordering: plus first, then unlabelled, then minus. Returns (new_gids, new_labels, boundary indices)."""
    order = np.argsort(-labels, kind="stable")  # +1 first, 0, then -1
    new_gids = gids[order]
    new_labels = labels[order]
    # Find boundaries
    n_plus = np.sum(new_labels == 1)
    n_unlabelled = np.sum(new_labels == 0)
    return new_gids, new_labels, order, n_plus, n_unlabelled


def _setup_matrix_axes(fig, gs_slot, has_labels):
    """Create the gridspec for a single matrix panel with optional label bars."""
    if has_labels:
        inner = gs_slot.subgridspec(
            2,
            2,
            width_ratios=[1, 30],
            height_ratios=[1, 20],
            hspace=0.02,
            wspace=0.02,
        )
        ax_main = fig.add_subplot(inner[1, 1])
        ax_top = fig.add_subplot(inner[0, 1], sharex=ax_main)
        ax_left = fig.add_subplot(inner[1, 0], sharey=ax_main)
        ax_corner = fig.add_subplot(inner[0, 0])
        ax_corner.axis("off")
        return ax_main, ax_top, ax_left
    else:
        ax_main = fig.add_subplot(gs_slot)
        return ax_main, None, None


def _draw_matrix_panel(
    ax_main,
    ax_top,
    ax_left,
    matrix,
    src_gids,
    tgt_gids,
    src_labels,
    tgt_labels,
    pre_label,
    post_label,
    title,
    src_boundary=None,
    tgt_boundary=None,
):
    """Draw one connectivity matrix with labels and optional separator lines."""
    ax_main.imshow(matrix != 0, aspect="auto", cmap="Greys", interpolation="none")

    # Tick labels = actual GIDs
    ax_main.set_xticks(range(len(tgt_gids)))
    ax_main.set_xticklabels(tgt_gids, fontsize=6, rotation=90)
    ax_main.set_yticks(range(len(src_gids)))
    ax_main.set_yticklabels(src_gids, fontsize=6)
    ax_main.set_xlabel(f"Target ({post_label})")
    ax_main.set_ylabel(f"Source ({pre_label})")
    ax_main.set_title(title, fontsize=10)

    # Color tick labels
    for i, lab in enumerate(tgt_labels):
        color = "#d6604d" if lab == 1 else "#4393c3" if lab == -1 else "black"
        ax_main.get_xticklabels()[i].set_color(color)
    for i, lab in enumerate(src_labels):
        color = "#d6604d" if lab == 1 else "#4393c3" if lab == -1 else "black"
        ax_main.get_yticklabels()[i].set_color(color)

    # Separator lines for reordered view
    if src_boundary is not None:
        ax_main.axhline(src_boundary - 0.5, color="green", linewidth=2, linestyle="--")
    if tgt_boundary is not None:
        ax_main.axvline(tgt_boundary - 0.5, color="green", linewidth=2, linestyle="--")

    # Label bars
    if ax_top is not None:
        _draw_label_bar(ax_top, tgt_labels, "h")
    if ax_left is not None:
        _draw_label_bar(ax_left, src_labels, "v")


def plot_connectivity(json_path: str):
    with open(json_path) as f:
        data = json.load(f)

    sources = np.array(data["sources"])
    targets = np.array(data["targets"])
    weights = np.array(data["weights"])
    pre_label = data["pre_label"]
    post_label = data["post_label"]

    if len(sources) == 0:
        print("No connections found.")
        return

    # Plus/minus GID sets (claimed — may be wrong)
    pre_plus = set(data.get("pre_plus_gids", []))
    pre_minus = set(data.get("pre_minus_gids", []))
    post_plus = set(data.get("post_plus_gids", []))
    post_minus = set(data.get("post_minus_gids", []))
    has_labels = bool(pre_plus or pre_minus or post_plus or post_minus)

    # Build connectivity matrix ordered by GID
    unique_src = np.sort(np.unique(sources))
    unique_tgt = np.sort(np.unique(targets))
    src_idx = {gid: i for i, gid in enumerate(unique_src)}
    tgt_idx = {gid: i for i, gid in enumerate(unique_tgt)}

    matrix = np.zeros((len(unique_src), len(unique_tgt)))
    for s, t, w in zip(sources, targets, weights):
        matrix[src_idx[s], tgt_idx[t]] = w

    src_labels = _label_array(unique_src, pre_plus, pre_minus)
    tgt_labels = _label_array(unique_tgt, post_plus, post_minus)

    # Summary counts
    n_pp = int(np.sum((matrix != 0)[np.ix_(src_labels == 1, tgt_labels == 1)]))
    n_pn = int(np.sum((matrix != 0)[np.ix_(src_labels == 1, tgt_labels == -1)]))
    n_np = int(np.sum((matrix != 0)[np.ix_(src_labels == -1, tgt_labels == 1)]))
    n_nn = int(np.sum((matrix != 0)[np.ix_(src_labels == -1, tgt_labels == -1)]))
    summary = f"+→+: {n_pp}   +→−: {n_pn}   −→+: {n_np}   −→−: {n_nn}"

    # --- Two panels: raw GID order + reordered by label ---
    fig = plt.figure(figsize=(20, 8))
    gs = fig.add_gridspec(1, 2, wspace=0.3)

    # Panel 1: raw GID order
    ax1, ax1_top, ax1_left = _setup_matrix_axes(fig, gs[0], has_labels)
    _draw_matrix_panel(
        ax1,
        ax1_top,
        ax1_left,
        matrix,
        unique_src,
        unique_tgt,
        src_labels,
        tgt_labels,
        pre_label,
        post_label,
        "Ordered by GID",
    )

    # Panel 2: reordered by claimed label
    if has_labels:
        src_sorted, src_lab_sorted, src_order, src_n_plus, _ = _sort_by_label(
            unique_src, src_labels
        )
        tgt_sorted, tgt_lab_sorted, tgt_order, tgt_n_plus, _ = _sort_by_label(
            unique_tgt, tgt_labels
        )
        matrix_reordered = matrix[np.ix_(src_order, tgt_order)]

        ax2, ax2_top, ax2_left = _setup_matrix_axes(fig, gs[1], True)
        _draw_matrix_panel(
            ax2,
            ax2_top,
            ax2_left,
            matrix_reordered,
            src_sorted,
            tgt_sorted,
            src_lab_sorted,
            tgt_lab_sorted,
            pre_label,
            post_label,
            "Grouped by claimed +/− label",
            src_boundary=src_n_plus,
            tgt_boundary=tgt_n_plus,
        )

    fig.suptitle(
        f"{pre_label} → {post_label}  ({len(sources)} connections)\n{summary}",
        fontsize=12,
    )
    plt.tight_layout()
    out_path = json_path.replace(".json", ".png")
    plt.savefig(out_path, dpi=150)
    print(f"Saved to {out_path}")
    print(summary)
    plt.show()

    # --- Label debug comparison ---
    label_debug = data.get("label_debug")
    if label_debug:
        print("\n" + "=" * 60)
        print("LABEL DEBUG: get_labelled index → GID mapping check")
        print("=" * 60)
        for model_name, dbg in label_debug.items():
            all_gids = dbg["all_gids"]
            plus_idx = dbg["plus_indices"]
            minus_idx = dbg["minus_indices"]
            plus_via_idx = dbg["plus_gids_via_index"]
            minus_via_idx = dbg["minus_gids_via_index"]
            n = dbg["n_total"]

            print(f"\n--- {model_name} (n={n}) ---")
            print(f"  all_gids:          {all_gids}")
            print(f"  plus_indices:      {plus_idx}")
            print(f"  minus_indices:     {minus_idx}")
            print(f"  plus  GIDs (indexed): {plus_via_idx}")
            print(f"  minus GIDs (indexed): {minus_via_idx}")

            # Check: do indices cover the full range without overlap?
            all_idx = sorted(plus_idx + minus_idx)
            expected = list(range(n))
            if all_idx == expected:
                print(f"  indices: OK — plus+minus covers [0, {n}) exactly")
            else:
                missing = set(expected) - set(all_idx)
                overlap = (
                    len(plus_idx) + len(minus_idx) - len(set(plus_idx + minus_idx))
                )
                print(f"  indices: PROBLEM")
                if missing:
                    print(f"    missing indices: {sorted(missing)}")
                    print(
                        f"    GIDs at missing indices: {[all_gids[i] for i in sorted(missing)]}"
                    )
                if overlap:
                    print(f"    {overlap} overlapping indices")

            # Check: do the stored PopView GIDs match what indexing gives?
            if model_name == "io":
                stored_plus = sorted(data.get("pre_plus_gids", []))
                stored_minus = sorted(data.get("pre_minus_gids", []))
            elif model_name == "purkinje_cell":
                stored_plus = sorted(data.get("post_plus_gids", []))
                stored_minus = sorted(data.get("post_minus_gids", []))
            else:
                continue

            indexed_plus = sorted(plus_via_idx)
            indexed_minus = sorted(minus_via_idx)
            if indexed_plus == stored_plus:
                print(f"  plus GIDs:  MATCH between indexing and stored PopView")
            else:
                print(f"  plus GIDs:  MISMATCH!")
                print(f"    via index:  {indexed_plus}")
                print(f"    in PopView: {stored_plus}")
            if indexed_minus == stored_minus:
                print(f"  minus GIDs: MATCH between indexing and stored PopView")
            else:
                print(f"  minus GIDs: MISMATCH!")
                print(f"    via index:  {indexed_minus}")
                print(f"    in PopView: {stored_minus}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <connectivity_debug.json>")
        sys.exit(1)
    plot_connectivity(sys.argv[1])
