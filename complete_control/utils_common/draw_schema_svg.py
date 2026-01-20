#!/usr/bin/env python3
"""
SVG template-based schema generation to visualize network activity.

Template file: schema_template.svg (in this directory)
Edit layout visually in Inkscape or other svg editor

Plot mapping: SVG placeholder IDs must match plot dictionary keys from merge_and_plot():
- Comma-separated IDs become tuple keys: id="planner_p,planner_n" → ("planner_p", "planner_n")
- Simple IDs become string keys: id="plan_to_inv" → "plan_to_inv"

Images are embedded with aspect-ratio preservation. Placeholder fill color shows as colored border.
Arrows are ignored, so include them as you want to see them.
"""

import base64
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import structlog
from config.paths import RunPaths
from config.plant_config import PlantConfig
from config.ResultMeta import ResultMeta
from neural.plot_utils import merge_and_plot
from plant.plant_plotting import ELBOW, plot_joint_space_animated
from utils_common.generate_signals import PlannerData
from utils_common.results import extract_and_merge_plant_results

log = structlog.get_logger(__name__)
template_path = Path(__file__).parent / "schema_template.svg"


def parse_plot_key_from_id(placeholder_id: str):
    """Convert SVG ID to plot dict key. Comma-separated IDs become tuples."""
    if "," in placeholder_id:
        return tuple(key.strip() for key in placeholder_id.split(","))
    else:
        return placeholder_id


def prep_temp_dir(run_paths: RunPaths):
    """Prepare temporary directory for plot files."""
    tmp_path = run_paths.figures / "figs_for_schema"
    if tmp_path.exists():
        shutil.rmtree(tmp_path)
    tmp_path.mkdir()
    return tmp_path


def embed_image_in_svg(
    svg_tree: ET.ElementTree,
    placeholder_id: str,
    image_path: Path,
    preserve_aspect: bool = True,
    padding: int = 5,
):
    """
    Embed an image into a placeholder rect, keeping the rect as a colored border.

    Args:
        svg_tree: Parsed SVG tree
        placeholder_id: ID of the placeholder rect
        image_path: Path to the image to embed
        preserve_aspect: If True, fit image within bounds preserving aspect ratio
        padding: Pixels of border to show around image (default: 5)
    """
    root = svg_tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Find the placeholder rect
    placeholder = root.find(f".//*[@id='{placeholder_id}']", ns) or root.find(
        f".//*[@id='{placeholder_id}']"
    )

    if placeholder is None:
        log.warning(f"Placeholder '{placeholder_id}' not found in template")
        return

    x = float(placeholder.get("x", 0))
    y = float(placeholder.get("y", 0))
    width = float(placeholder.get("width", 100))
    height = float(placeholder.get("height", 100))

    # Read and encode image
    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("ascii")

    if preserve_aspect:
        from PIL import Image

        img = Image.open(image_path)
        img_width, img_height = img.size
        img_aspect = img_width / img_height
        box_aspect = width / height

        if img_aspect > box_aspect:
            # Image is wider - fit to width
            new_width = width
            new_height = width / img_aspect
            new_x = x
            new_y = y + (height - new_height) / 2
        else:
            # Image is taller - fit to height
            new_height = height
            new_width = height * img_aspect
            new_x = x + (width - new_width) / 2
            new_y = y
    else:
        new_x, new_y = x, y
        new_width, new_height = width, height

    # padding to create border effect
    new_x += padding
    new_y += padding
    new_width -= 2 * padding
    new_height -= 2 * padding

    # image element
    ns_map = {
        None: "http://www.w3.org/2000/svg",
        "xlink": "http://www.w3.org/1999/xlink",
    }

    # Register namespaces
    for prefix, uri in ns_map.items():
        ET.register_namespace(prefix if prefix else "", uri)

    image_elem = ET.Element(
        "{http://www.w3.org/2000/svg}image",
        {
            "x": str(new_x),
            "y": str(new_y),
            "width": str(new_width),
            "height": str(new_height),
            "{http://www.w3.org/1999/xlink}href": f"data:image/png;base64,{img_data}",
        },
    )

    # find parent, add image on top (z-axis)
    parent = None
    for p in root.iter():
        if placeholder in list(p):
            parent = p
            break

    if parent is not None:
        idx = list(parent).index(placeholder)
        parent.insert(idx + 1, image_elem)
    else:
        log.warning(f"Could not find parent for placeholder '{placeholder_id}'")


def create_schema_from_template(
    tree: ET.ElementTree, output_path: Path, id2plot_path: dict[str, Path]
):
    """
    Generate final schema by inserting plots into SVG template.

    Args:
        tree: Parsed SVG template tree
        output_path: Where to save final SVG
        id2plot_path: Dict mapping placeholder_id -> plot image path
    """
    for placeholder_id, plot_path in id2plot_path.items():
        if plot_path and plot_path.exists():
            embed_image_in_svg(tree, placeholder_id, plot_path, preserve_aspect=True)
        else:
            log.warning(f"Plot not found for '{placeholder_id}': {plot_path}")

    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    log.info(f"Saved schema to {output_path}")


def generate_joint_space_plot(metas: list[ResultMeta], figs_path: Path) -> Path:
    """Generate joint space plot from simulation results."""
    plant_data = extract_and_merge_plant_results(metas)
    params = [m.load_params() for m in metas]
    ref_mp = params[0]
    time_vector_total_s = np.arange(
        0,
        sum(p_item.simulation.duration_s for p_item in params),
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
    return joint_plot_path


def draw_schema(metas: list[ResultMeta]):
    """
    Generate controller schema visualization using SVG template.

    Args:
        metas: List of ResultMeta objects from simulation runs
    """
    run_paths = metas[-1].load_params().run_paths
    figs_path = prep_temp_dir(run_paths)
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    log.info("Generating individual population plots...")
    p = merge_and_plot(metas, path_fig=figs_path)

    log.info("Generating joint space plot...")
    joint_plot_path = generate_joint_space_plot(metas, figs_path)

    log.info("Mapping plots to template placeholders...")
    tree = ET.parse(template_path)
    root = tree.getroot()

    id2plot_path = {}

    for elem in root.iter():
        placeholder_id = elem.get("id")
        if not placeholder_id:
            continue

        if placeholder_id == "joint_space_plot":
            id2plot_path[placeholder_id] = joint_plot_path
            continue

        plot_key = parse_plot_key_from_id(placeholder_id)

        if plot_key in p:
            plot_path = p[plot_key][2]
            id2plot_path[placeholder_id] = plot_path

    log.info(f"Mapped {len(id2plot_path)} plots to template placeholders")

    output_svg = run_paths.figures_receiver / "whole_controller_schema.svg"
    create_schema_from_template(tree, output_svg, id2plot_path)

    log.info(f"Schema generation complete: {output_svg}")

    import cairosvg

    output_png = output_svg.with_suffix(".png")
    cairosvg.svg2png(url=str(output_svg), write_to=str(output_png), output_height=4000)
    log.info(f"Exported PNG: {output_png}")
