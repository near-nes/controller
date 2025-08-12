import io
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# --- Data ---
SRC = Path(".") / "det_logs" / "weight_1&freq_max450.txt"
PLOT_FILENAME = "rb_sens_weight_1&freq_max450.png"
FIG_FOLDER = Path(".") / "res"


def parse_and_plot_rbf_data(data):
    pattern = re.compile(
        r"in_rate:\s*([\d\.]+)\s*out_rate:\s*([\d\.]+)\s*sens:\s*(-?[\d\.]+)"
    )

    out_rates = []
    sens_values = []
    in_rates = []

    buf = io.StringIO(data)
    for line in buf:
        match = pattern.search(line)
        if match:
            in_rates.append(float(match.group(1)))
            out_rates.append(float(match.group(2)))
            sens_values.append(float(match.group(3)))

    if not out_rates:
        print("No data found. Cannot generate plot.")
        return

    # --- Plotting ---
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    # Create a scatter plot of output rate vs. sensitivity
    ax.scatter(
        sens_values,
        out_rates,
        label=f"Neuron Responses for input rates [{min(in_rates)},{max(in_rates)}]",
        color="mediumvioletred",
        s=10,
        zorder=5,
    )

    # Also plot as a line to better visualize the curve shape
    # Sort values by sensitivity to ensure the line plot is drawn correctly
    # sorted_pairs = sorted(zip(sens_values, out_rates))
    # sorted_sens, sorted_out_rates = zip(*sorted_pairs)
    # ax.plot(
    #     sorted_sens,
    #     sorted_out_rates,
    #     color="lightcoral",
    #     linestyle="--",
    #     alpha=0.8,
    #     zorder=4,
    # )

    # Set the title and labels for the axes
    ax.set_title("Neuron Tuning Curve (RBF Response)", fontsize=18, pad=20)
    ax.set_xlabel("Neuron Sensitivity (Preferred Input)", fontsize=14)
    ax.set_ylabel("Output Rate", fontsize=14)

    ax.legend(fontsize=12)
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    plt.show()
    plt.savefig(FIG_FOLDER / PLOT_FILENAME)


if __name__ == "__main__":
    with open(SRC) as f:
        log_data = f.read()
    parse_and_plot_rbf_data(log_data)
