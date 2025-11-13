from pathlib import Path
import datetime, random, string
from config.ResultMeta import ResultMeta
from config.MasterParams import MasterParams
from config import paths


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
    if len(p) is not 1:
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
