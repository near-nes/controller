import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Rectangle, FancyArrow
from pathlib import Path
from config.plant_config import PlantConfig
from config.paths import RunPaths
import structlog
import contextlib

log = structlog.get_logger(__name__)


def draw_schema(run_paths: RunPaths, scale_factor: float = 0.005):

    fig, ax = plt.subplots(figsize=(40, 35))
    ax.set_facecolor("#fefbf3")
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 35)
    ax.axis("off")

    # This function embeds an image into the plot at specified coordinates
    # It also adds a border around the image
    def embed_image(ax, img_path, x, y, w, h):
        if img_path and img_path.exists():
            try:
                with contextlib.redirect_stdout(None), contextlib.redirect_stderr(None):
                    img = mpimg.imread(img_path)
                border = Rectangle(
                    (x, y), w, h, fill=False, edgecolor="black", linewidth=1.5, zorder=3
                )
                ax.add_patch(border)
                pad = 0.05 * min(w, h)
                ax.imshow(
                    img,
                    extent=[x + pad, x + w - pad, y + pad, y + h - pad],
                    aspect="auto",
                    zorder=2,
                )
            except Exception as e:
                log.error(f"Error: con not be implemented{img_path}", error=e)
        elif img_path:
            log.warning(f"Warning: images can not be found in {img_path}.")

        # Find the latest run directory

    neural_figs_path = run_paths.figures
    robotic_figs_path = run_paths.figures_receiver
    print(f"Neural figures path: {neural_figs_path}")
    log.info(f"Taking all images: {neural_figs_path.name} and {robotic_figs_path.name}")

    components_raw = {
        "Inverse model_container": (
            10.0,
            20.0,
            18,
            9.5,
            "#ffcc66",
            "Inverse model",
            "black",
            12,
            None,
        ),
        "Motor Cortex_container": (
            10.0,
            10.0,
            12.0,
            9.5,
            "#99ff33",
            "Motor Cortex",
            "black",
            12,
            None,
        ),
        "Forward model_container": (
            10,
            0.0,
            18,
            9.5,
            "#ff6666",
            "Forward model",
            "black",
            12,
            None,
        ),
        "Brain Stem_container": (
            24.0,
            12.5,
            9.0,
            5.0,
            "#A9A9A9",
            "Brain Stem",
            "black",
            12,
            None,
        ),
        "Planner": (
            1.0,
            17.0,
            8.0,
            5.0,
            "#ff9933",
            "",
            "",
            0,
            neural_figs_path / "planner_0.png",
        ),
        "plan to inv": (
            1.0,
            23.0,
            8.0,
            5.0,
            "#ff9933",
            "",
            "",
            0,
            neural_figs_path / "cereb_plan_to_inv_0.png",
        ),
        "error inv": (
            4.5,
            13,
            8.0,
            5.0,
            "#e066ff",
            "",
            "",
            0,
            neural_figs_path / "cereb_error_inv_0.png",
        ),
        "State": (
            1.0,
            5.0,
            8.0,
            5.0,
            "#99ccff",
            "",
            "",
            0,
            neural_figs_path / "state_0.png",
        ),
        "state to inv": (
            1.0,
            9.0,
            8.0,
            5.0,
            "#99ccff",
            "",
            "",
            0,
            neural_figs_path / "cereb_state_to_inv_0.png",
        ),
        "prediction": (
            1.0,
            1.0,
            8.0,
            5.0,
            "#ff6666",
            "",
            "",
            0,
            neural_figs_path / "pred_0.png",
        ),
        "motor prediction": (
            29.0,
            23.0,
            8.0,
            5.0,
            "#e066ff",
            "",
            "",
            0,
            neural_figs_path / "cereb_motor_prediction_0.png",
        ),
        "motor commands": (
            29.5,
            9.0,
            8.0,
            5.0,
            "#99ff33",
            "",
            "",
            0,
            neural_figs_path / "cereb_motor_commands_0.png",
        ),
        "error forw": (
            29.5,
            3.0,
            8.0,
            5.0,
            "#ff0066",
            "",
            "",
            0,
            neural_figs_path / "cereb_error_0.png",
        ),
        "Sensory feedback": (
            35.0,
            5.0,
            8.0,
            5.0,
            "#66cc33",
            "",
            "",
            0,
            neural_figs_path / "sensoryneur_0.png",
        ),
        "feedback": (
            35.0,
            1.0,
            8.0,
            5.0,
            "#66cc33",
            "",
            "",
            0,
            neural_figs_path / "cereb_feedback_0.png",
        ),
        "Human Figure Plot": (
            35.0,
            15.0,
            8.0,
            7.5,
            "none",
            "",
            "",
            0,
            next(robotic_figs_path.glob(f"position_joint*.png"), None),
        ),
        # Inverse Model
        "Mf_inv": (
            11.0,
            25.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "cereb_core_inv_mf_0.png",
        ),
        "PC_inv": (
            16.5,
            23.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "cereb_core_inv_pc_0.png",
        ),
        "DCN_inv": (
            23.0,
            23.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "cereb_core_inv_dcnp_0.png",
        ),
        "IO_inv": (
            11.0,
            21.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "cereb_core_inv_io_0.png",
        ),
        # --- Motor Cortex ---
        "Ffwd": (
            11.0,
            16.0,
            8.0,
            5.0,
            "#66cc33",
            "Ffwd",
            "black",
            12,
            neural_figs_path / "mc_ffwd_0.png",
        ),
        "Out": (
            16.0,
            14.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "mc_out_0.png",
        ),
        "Fbk": (
            11.0,
            11.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "fbk_smooth_0.png",
        ),
        # --- Brain Stem ---
        "Smoothing": (
            26.5,
            13.5,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "brainstem_0.png",
        ),
        # --- Forward Model ---
        "DCN_forw": (
            10.5,
            2.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "cereb_core_forw_dcnp_0.png",
        ),
        "PC_forw": (
            16.5,
            2.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "cereb_core_forw_pc_0.png",
        ),
        "Mf_forw": (
            22.0,
            6.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "cereb_core_forw_mf_0.png",
        ),
        "IO_forw": (
            22.0,
            1.0,
            8.0,
            5.0,
            "none",
            "",
            "",
            0,
            neural_figs_path / "cereb_core_forw_io_0.png",
        ),
    }
    # Dynamically Calculate Component Sizes
    components = {}
    for name, (
        x,
        y,
        initial_w,
        initial_h,
        color,
        text,
        text_color,
        font_size,
        plot_file,
    ) in components_raw.items():
        w, h = initial_w, initial_h
        if plot_file and plot_file.exists():
            try:
                with contextlib.redirect_stdout(None), contextlib.redirect_stderr(None):
                    img = mpimg.imread(plot_file)
                height_px, width_px, _ = img.shape
                w = width_px * scale_factor
                h = height_px * scale_factor
            except Exception as e:
                log.warning(f"Warning: can not be found {plot_file} ", error=e)

        components[name] = (x, y, w, h, color, text, text_color, font_size, plot_file)

    # Draw rectangles
    for name, (
        x,
        y,
        w,
        h,
        color,
        text,
        text_color,
        font_size,
        plot_file,
    ) in components.items():
        is_container = name.endswith("_container")

        if color != "none":
            rect = Rectangle(
                (x, y),
                w,
                h,
                facecolor=color,
                edgecolor="black",
                linewidth=1.5,
                zorder=1,
            )
            ax.add_patch(rect)

        if plot_file:
            embed_image(ax, plot_file, x, y, w, h)

        if is_container:
            ax.text(
                x + w / 2,
                y + h + 0.15,
                text,
                ha="center",
                va="bottom",
                color=text_color,
                fontsize=font_size,
                zorder=5,
            )

    # --- MUSIC ---
    ax.plot([34.5, 34.5], [0, 35], color="blue", linestyle="--", linewidth=1.5)
    ax.text(
        33.5,
        33.5,
        "MUSIC\ninterface",
        rotation=90,
        va="center",
        ha="left",
        color="blue",
        fontsize=12,
    )

    # Draw arrows
    arrow_props = dict(
        width=0.025,
        length_includes_head=True,
        head_width=0.2,
        head_length=0.3,
        zorder=4,
        fc="black",
        ec="black",
    )

    def draw_path(path_points, color):
        path_x, path_y = zip(*path_points)
        ax.plot(path_x, path_y, color=color, linewidth=2, zorder=4)
        dx = path_x[-1] - path_x[-2]
        dy = path_y[-1] - path_y[-2]
        ax.add_patch(
            FancyArrow(path_x[-2], path_y[-2], dx, dy, color=color, **arrow_props)
        )

    # Drawing paths between components
    paths = {
        "planner_to_plan_inv": [
            (
                components["Planner"][0] + components["Planner"][2] / 2,
                components["Planner"][1] + components["Planner"][3],
            ),
            (
                components["plan to inv"][0] + components["plan to inv"][2] / 2,
                components["plan to inv"][1],
            ),
        ],
        "plan_inv_to_mf": [
            (
                components["plan to inv"][0] + components["plan to inv"][2],
                components["plan to inv"][1] + 1.5,
            ),
            (components["Mf_inv"][0] - 1, components["plan to inv"][1] + 1.5),
            (
                components["Mf_inv"][0] - 1,
                components["Mf_inv"][1] + components["Mf_inv"][3] / 2,
            ),
            (
                components["Mf_inv"][0],
                components["Mf_inv"][1] + components["Mf_inv"][3] / 2,
            ),
        ],
        "plan_inv_to_error_inv": [
            (
                components["plan to inv"][0] + components["plan to inv"][2],
                components["plan to inv"][1] + 0.5,
            ),
            (components["error inv"][0] + 2, components["plan to inv"][1] + 0.5),
            (
                components["error inv"][0] + 2,
                components["error inv"][1] + components["error inv"][3],
            ),
            (
                components["error inv"][0] + components["error inv"][2] / 2,
                components["error inv"][1] + components["error inv"][3],
            ),
        ],
        "planner_to_fbk": [
            (
                components["Planner"][0],
                components["Planner"][1] + components["Planner"][3] / 2,
            ),
            (0.5, components["Planner"][1] + components["Planner"][3] / 2),
            (0.5, components["Fbk"][1] + components["Fbk"][3] / 2),
            (components["Fbk"][0], components["Fbk"][1] + components["Fbk"][3] / 2),
        ],
        "error_inv_to_io": [
            (
                components["error inv"][0] + components["error inv"][2],
                components["error inv"][1] + components["error inv"][3] / 2,
            ),
            (
                components["IO_inv"][0],
                components["IO_inv"][1] + components["IO_inv"][3] / 2,
            ),
        ],
        "state_to_state_inv": [
            (
                components["State"][0] + components["State"][2] / 2,
                components["State"][1] + components["State"][3],
            ),
            (
                components["state to inv"][0] + components["state to inv"][2] / 2,
                components["state to inv"][1],
            ),
        ],
        "state_to_fbk": [
            (
                components["State"][0] + components["State"][2],
                components["State"][1] + components["State"][3] / 2,
            ),
            (components["Fbk"][0], components["Fbk"][1] + components["Fbk"][3] / 2),
        ],
        "state_inv_to_error_inv": [
            (
                components["state to inv"][0] + components["state to inv"][2],
                components["state to inv"][1] + components["state to inv"][3] / 2,
            ),
            (
                components["state to inv"][0] + components["state to inv"][2] + 1,
                components["state to inv"][1] + components["state to inv"][3] / 2,
            ),
            (
                components["state to inv"][0] + components["state to inv"][2] + 1,
                components["error inv"][1],
            ),
            (
                components["error inv"][0] + components["error inv"][2] / 2,
                components["error inv"][1],
            ),
        ],
        "prediction_to_state": [
            (
                components["prediction"][0] + components["prediction"][2] / 2,
                components["prediction"][1] + components["prediction"][3],
            ),
            (
                components["State"][0] + components["State"][2] / 2,
                components["State"][1],
            ),
        ],
        "dcn_forw_to_prediction": [
            (
                components["DCN_forw"][0],
                components["DCN_forw"][1] + components["DCN_forw"][3] / 2,
            ),
            (
                components["prediction"][0] + components["prediction"][2],
                components["prediction"][1] + components["prediction"][3] / 2,
            ),
        ],
        "dcn_inv_to_motor_pred": [
            (
                components["DCN_inv"][0] + components["DCN_inv"][2],
                components["DCN_inv"][1] + components["DCN_inv"][3] / 2,
            ),
            (
                components["motor prediction"][0],
                components["motor prediction"][1]
                + components["motor prediction"][3]
                - 1,
            ),
        ],
        "motor_pred_to_smoothing": [
            (
                components["motor prediction"][0]
                + components["motor prediction"][2] / 2,
                components["motor prediction"][1],
            ),
            (
                components["Smoothing"][0] + components["Smoothing"][2] / 2,
                components["Smoothing"][1] + components["Smoothing"][3],
            ),
        ],
        "out_to_smoothing": [
            (
                components["Out"][0] + components["Out"][2],
                components["Out"][1] + components["Out"][3] / 2,
            ),
            (
                components["Smoothing"][0],
                components["Smoothing"][1] + components["Smoothing"][3] / 2,
            ),
        ],
        "out_to_motor_commands": [
            (components["Out"][0] + components["Out"][2] / 2, components["Out"][1]),
            (
                components["Out"][0] + components["Out"][2] / 2,
                components["motor commands"][1] + components["motor commands"][3],
            ),
            (
                components["motor commands"][0],
                components["motor commands"][1] + components["motor commands"][3] / 2,
            ),
        ],
        "motor_commands_to_mf_forw": [
            (
                components["motor commands"][0],
                components["motor commands"][1] + components["motor commands"][3] / 2,
            ),
            (
                components["Mf_forw"][0] + components["Mf_forw"][2],
                components["Mf_forw"][1] + components["Mf_forw"][3] / 2,
            ),
        ],
        "dcn_forw_to_error_forw": [
            (
                components["DCN_forw"][0],
                components["DCN_forw"][1] + components["DCN_forw"][3] / 2,
            ),
            (9.5, components["DCN_forw"][1] + components["DCN_forw"][3] / 2),
            (9.5, 1),
            (components["error forw"][0] + components["error forw"][2] / 2, 1),
            (
                components["error forw"][0] + components["error forw"][2] / 2,
                components["error forw"][1],
            ),
        ],
        "error_forw_to_io_forw": [
            (
                components["error forw"][0],
                components["error forw"][1] + components["error forw"][3] / 2,
            ),
            (
                components["IO_forw"][0] + components["IO_forw"][2],
                components["IO_forw"][1] + components["IO_forw"][3] / 2,
            ),
        ],
        "feedback_to_error_forw": [
            (
                components["feedback"][0],
                components["feedback"][1] + components["feedback"][3] / 2,
            ),
            (
                components["error forw"][0] + components["error forw"][2],
                components["error forw"][1] + components["error forw"][3] / 2,
            ),
        ],
        "smoothing_to_human": [
            (
                components["Smoothing"][0] + components["Smoothing"][2],
                components["Smoothing"][1] + components["Smoothing"][3] / 2,
            ),
            (
                components["Human Figure Plot"][0],
                components["Human Figure Plot"][1]
                + components["Human Figure Plot"][3] / 2,
            ),
        ],
        "human_to_sensory": [
            (
                components["Human Figure Plot"][0]
                + components["Human Figure Plot"][2] / 2,
                components["Human Figure Plot"][1],
            ),
            (
                components["Sensory feedback"][0]
                + components["Sensory feedback"][2] / 2,
                components["Sensory feedback"][1] + components["Sensory feedback"][3],
            ),
        ],
        "sensory_to_feedback": [
            (
                components["Sensory feedback"][0]
                + components["Sensory feedback"][2] / 2,
                components["Sensory feedback"][1],
            ),
            (
                components["feedback"][0] + components["feedback"][2] / 2,
                components["feedback"][1] + components["feedback"][3],
            ),
        ],
    }

    draw_path(paths["planner_to_plan_inv"], "dimgray")
    draw_path(paths["plan_inv_to_mf"], "dimgray")
    draw_path(paths["plan_inv_to_error_inv"], "dimgray")
    draw_path(paths["planner_to_fbk"], "dimgray")
    draw_path(paths["error_inv_to_io"], "orchid")
    draw_path(paths["state_to_state_inv"], "dimgray")
    draw_path(paths["state_to_fbk"], "royalblue")
    draw_path(paths["state_inv_to_error_inv"], "royalblue")
    draw_path(paths["prediction_to_state"], "red")
    draw_path(paths["dcn_forw_to_prediction"], "red")
    draw_path(paths["dcn_inv_to_motor_pred"], "gold")
    draw_path(paths["motor_pred_to_smoothing"], "orchid")
    draw_path(paths["out_to_smoothing"], "lightseagreen")
    draw_path(paths["out_to_motor_commands"], "lightseagreen")
    draw_path(paths["motor_commands_to_mf_forw"], "yellowgreen")
    draw_path(paths["dcn_forw_to_error_forw"], "red")
    draw_path(paths["error_forw_to_io_forw"], "deeppink")
    draw_path(paths["feedback_to_error_forw"], "dimgray")
    draw_path(paths["smoothing_to_human"], "dimgray")
    draw_path(paths["human_to_sensory"], "black")
    draw_path(paths["sensory_to_feedback"], "black")

    filepath = robotic_figs_path / f"whole_controller_schema.png"

    plt.savefig(filepath, bbox_inches="tight", dpi=300, facecolor=ax.get_facecolor())
    plt.close(fig)
