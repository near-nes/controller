import contextlib
import shutil

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import structlog
from config.paths import RunPaths
from config.plant_config import PlantConfig
from config.ResultMeta import ResultMeta
from matplotlib.patches import FancyArrow, Rectangle
from neural.plot_utils import merge_and_plot
from neural.population_utils import POPS
from plant.plant_plotting import ELBOW, plot_joint_space_animated
from utils_common.generate_signals import PlannerData
from utils_common.results import extract_and_merge_plant_results

log = structlog.get_logger(__name__)


def prep_temp_dir(run_paths: RunPaths):
    tmp_path = run_paths.figures / "figs_for_schema"
    if tmp_path.exists():
        shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    return tmp_path


def draw_schema(metas: list[ResultMeta], scale_factor: float = 0.005):
    run_paths = metas[-1].load_params().run_paths
    figs_path = prep_temp_dir(run_paths)

    p = merge_and_plot(metas, path_fig=figs_path)

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

    # Generate Joint Space Plot
    plant_data = extract_and_merge_plant_results(metas)
    params = [i.load_params() for i in metas]
    ref_mp = params[0]
    time_vector_total_s = np.arange(
        0,
        sum(p.simulation.duration_s for p in params),
        params[0].simulation.resolution / 1000,
    )
    ref_plant_config = PlantConfig(ref_mp)
    joint_data = plant_data.joint_data[ELBOW]

    run_paths_list = [RunPaths.from_run_id(m.id) for m in metas]
    trjs = []
    for rp in run_paths_list:
        with open(rp.trajectory, "r") as f:
            planner_data: PlannerData = PlannerData.model_validate_json(f.read())
            trjs.append(planner_data.trajectory)
    desired_trajectory = np.concatenate(trjs, axis=0)

    _, _, joint_plot_path = plot_joint_space_animated(
        pth_fig_receiver=figs_path,
        time_vector_s=time_vector_total_s,
        pos_j_rad_actual=joint_data.pos_rad,
        desired_trj_joint_rad=desired_trajectory,
        animated=False,
        save_fig=True,
    )

    # Mapping from component name to p key
    p_map = {
        "Planner": ("planner_p", "planner_n"),
        "plan to inv": "plan_to_inv",
        "error inv": ("error_inv_p", "error_inv_n"),
        "State": ("state_p", "state_n"),
        "state to inv": ("state_to_inv_p", "state_to_inv_n"),
        "prediction": ("pred_p", "pred_n"),
        "motor prediction": ("motor_prediction_p", "motor_prediction_n"),
        "motor commands": "motor_commands",
        "error forw": ("error_p", "error_n"),
        "Sensory feedback": ("sn_p", "sn_n"),
        "feedback": ("feedback_p", "feedback_n"),
        "Mf_inv": "inv_mf",
        "PC_inv": ("inv_pc_p", "inv_pc_n"),
        "DCN_inv": ("inv_dcnp_p", "inv_dcnp_n"),
        "IO_inv": ("inv_io_p", "inv_io_n"),
        "Ffwd": ("mc_M1_p", "mc_M1_n"),
        "Out": ("mc_out_p", "mc_out_n"),
        "Fbk": ("mc_fbk_p", "mc_fbk_n"),
        "Smoothing": ("brainstem_p", "brainstem_n"),
        "DCN_forw": ("forw_dcnp_p", "forw_dcnp_n"),
        "PC_forw": ("forw_pc_p", "forw_pc_n"),
        "Mf_forw": "forw_mf",
        "IO_forw": ("forw_io_p", "forw_io_n"),
    }

    def get_p_path(name):
        key = p_map.get(name)
        if key and key in p:
            return p[key][2]
        return None

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
            get_p_path("Planner"),
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
            get_p_path("plan to inv"),
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
            get_p_path("error inv"),
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
            get_p_path("State"),
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
            get_p_path("state to inv"),
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
            get_p_path("prediction"),
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
            get_p_path("motor prediction"),
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
            get_p_path("motor commands"),
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
            get_p_path("error forw"),
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
            get_p_path("Sensory feedback"),
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
            get_p_path("feedback"),
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
            (
                next(robotic_figs_path.glob(f"position_joint*.png"), None)
                if joint_plot_path is None
                else joint_plot_path
            ),
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
            get_p_path("Mf_inv"),
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
            get_p_path("PC_inv"),
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
            get_p_path("DCN_inv"),
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
            get_p_path("IO_inv"),
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
            get_p_path("Ffwd"),
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
            get_p_path("Out"),
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
            get_p_path("Fbk"),
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
            get_p_path("Smoothing"),
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
            get_p_path("DCN_forw"),
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
            get_p_path("PC_forw"),
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
            get_p_path("Mf_forw"),
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
            get_p_path("IO_forw"),
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
        "plan_to_error_inv": [
            (
                components["Planner"][0] + components["Planner"][2],
                components["Planner"][1] + 0.5,
            ),
            (components["error inv"][0] + 2, components["Planner"][1] + 0.5),
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
    draw_path(paths["plan_to_error_inv"], "dimgray")
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
    log.info(f"saved complete schema at {filepath}")
    plt.close(fig)
