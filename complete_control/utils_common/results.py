import datetime
import random
import string
from pathlib import Path

import numpy as np
from config import paths
from config.MasterParams import MasterParams
from config.ResultMeta import ResultMeta
from plant.plant_models import EEData, JointData, PlantPlotData


def make_trial_id(
    timestamp_str: str | None = None,
    label: str = "trial",
    suffix_len: int = 4,
):
    """Return a readable, time-sortable trial ID."""
    timestamp_str = timestamp_str or datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=suffix_len)
    )
    return f"{timestamp_str}_{suffix}-{label}"


def read_weights(master_params: MasterParams) -> list[Path] | None:
    parent_id = master_params.parent_id
    if len(parent_id) == 0:
        return None

    p = [i for i in paths.RUNS_DIR.glob(f"{parent_id}*") if i.is_dir()]
    if len(p) != 1:
        raise ValueError(f"found {len(p)} parent(s) for key='{parent_id}'")

    rp = paths.RunPaths.from_run_id(p[0].name, create_if_not_present=False)
    with open(rp.meta_result, "r") as f:
        res = ResultMeta.model_validate_json(f.read())
    with open(rp.params_json, "r") as f:
        par = MasterParams.model_validate_json(f.read())

    if not par.USE_CEREBELLUM or not (par.USE_MUSIC == master_params.USE_MUSIC):
        raise ValueError(f"specified run unsuitable for param loading")

    neural = res.load_neural()
    return neural.weights


def gather_metas(id: str):
    meta = ResultMeta.from_id(id)
    if meta.parent is None or len(meta.parent) == 0:
        return [meta]
    return [meta, *gather_metas(meta.parent)]


def extract_and_merge_plant_results(results: list[ResultMeta]):
    data = [r.load_robotic() for r in results]
    if not data:
        raise ValueError("Empty results")
    return PlantPlotData(
        joint_data=[
            JointData(
                pos_rad=np.concatenate([d.joint_data[i].pos_rad for d in data]),
                vel_rad_s=np.concatenate([d.joint_data[i].vel_rad_s for d in data]),
                input_cmd_torque=np.concatenate(
                    [d.joint_data[i].input_cmd_torque for d in data]
                ),
            )
            for i in range(len(data[0].joint_data))
        ],
        ee_data=EEData(
            pos_ee=np.concatenate([d.ee_data.pos_ee for d in data]),
            vel_ee=np.concatenate([d.ee_data.vel_ee for d in data]),
        ),
        error=[d.error[0] for d in data],
        init_hand_pos_ee=data[0].init_hand_pos_ee,
        trgt_hand_pos_ee=data[0].trgt_hand_pos_ee,
    )
