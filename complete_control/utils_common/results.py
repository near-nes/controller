import datetime
import random
import string
from pathlib import Path
from typing import Optional, Type, TypeVar

import numpy as np
from config import paths
from config.MasterParams import MasterParams
from config.ResultMeta import ResultMeta
from neural.CerebellumHandlerPopulations import CerebellumHandlerPopulationsRecordings
from neural.CerebellumPopulations import CerebellumPopulationsRecordings
from neural.ControllerPopulations import ControllerPopulationsRecordings
from neural.neural_models import PopulationSpikes
from neural.result_models import NeuralResultManifest
from plant.plant_models import EEData, JointData, PlantPlotData
from pydantic import BaseModel
from utils_common.generate_signals import PlannerData


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


def extract_time_move_trajectories(ms: list[ResultMeta]):
    data = [r.load_robotic() for r in ms]
    params = [r.load_params() for r in ms]
    desired = []
    for rp in [p.run_paths for p in params]:
        with open(rp.trajectory, "r") as f:
            planner_data: PlannerData = PlannerData.model_validate_json(f.read())
            desired.append(planner_data.trajectory)
    time_move_effective_shoulder_trajs = []
    time_move_desired_shoulder_trajs = []
    for d, des, p in zip(data, desired, params):
        start = int(p.simulation.time_prep / p.simulation.resolution)
        end = int(
            (p.simulation.time_prep + p.simulation.time_move) / p.simulation.resolution
        )
        time_move_effective_shoulder_trajs.append(d.joint_data[1].pos_rad[start:end])
        time_move_desired_shoulder_trajs.append(des[start:end])

    return (
        time_move_effective_shoulder_trajs,
        time_move_desired_shoulder_trajs,
    )


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


def concatenate_population_spikes(
    pops: list[Optional[PopulationSpikes]],
    trial_duration_ms: list[float],
) -> Optional[PopulationSpikes]:
    """
    Concatenate multiple PopulationSpikes objects.

    - Keeps gids, population_size, neuron_model, and label the same (from first non-None)
    - Concatenates senders array, shifts times array by duration
    - Returns None if all inputs are None
    """
    # Filter out None values
    valid_pops = [p for p in pops if p is not None]

    if not valid_pops:
        return None

    # Use first population as reference
    ref = valid_pops[0]

    # Validate that all populations have the same metadata
    for pop in valid_pops[1:]:
        if not (pop.gids == ref.gids).all():
            raise ValueError(f"GIDs mismatch for population '{ref.label}'")
        if pop.population_size != ref.population_size:
            raise ValueError(f"Population size mismatch for '{ref.label}'")
        if pop.neuron_model != ref.neuron_model:
            raise ValueError(f"Neuron model mismatch for '{ref.label}'")
        if pop.label != ref.label:
            raise ValueError(f"Label mismatch: '{pop.label}' vs '{ref.label}'")

    # Concatenate spike data
    import numpy as np

    all_senders = np.concatenate([p.senders for p in valid_pops])
    all_times = np.concatenate(  # shift times according to trial duration
        [p.times + i * d for p, (i, d) in zip(valid_pops, enumerate(trial_duration_ms))]
    )

    return PopulationSpikes(
        label=ref.label,
        gids=ref.gids,
        senders=all_senders,
        times=all_times,
        population_size=ref.population_size,
        neuron_model=ref.neuron_model,
    )


T = TypeVar("T", bound=BaseModel)


def concatenate_population_recordings(
    recordings: list[Optional[T]],
    recording_type: Type[T],
    trial_durations_ms: list[float],
) -> Optional[T]:
    """
    Generic function to concatenate population recordings.

    Works for ControllerPopulationsRecordings, CerebellumPopulationsRecordings,
    and CerebellumHandlerPopulationsRecordings.

    Args:
        recordings: List of recording objects (can contain None values)
        recording_type: The class type to instantiate (e.g., ControllerPopulationsRecordings)

    Returns:
        Concatenated recording object, or None if all inputs are None
    """
    valid_recordings = [r for r in recordings if r is not None]

    if not valid_recordings:
        return None

    field_names = recording_type.model_fields.keys()
    concatenated_data = {}
    for field in field_names:
        pops = [getattr(rec, field) for rec in valid_recordings]
        concatenated_pop = concatenate_population_spikes(pops, trial_durations_ms)
        concatenated_data[field] = (
            concatenated_pop.model_dump() if concatenated_pop is not None else None
        )

    return recording_type(**concatenated_data)


def concatenate_neural_results(
    result_metas: list[ResultMeta],
) -> NeuralResultManifest:
    """
    Concatenates NeuralResultManifest, shifting times by trial duration (different durations are ok).
    Verifies consistent GIDs, label, neuron model, population size.
    """
    if not result_metas:
        raise ValueError("Cannot concatenate empty list of ResultMeta")

    neural_results = [meta.load_neural() for meta in result_metas]
    trial_durations_ms = [
        meta.load_params().simulation.duration_ms for meta in result_metas
    ]

    use_cerebellum_values = [nr.use_cerebellum for nr in neural_results]
    if len(set(use_cerebellum_values)) > 1:
        raise ValueError(
            f"Inconsistent use_cerebellum values: {use_cerebellum_values}. "
            "All results must have the same use_cerebellum setting."
        )

    controller = concatenate_population_recordings(
        [nr.controller for nr in neural_results],
        ControllerPopulationsRecordings,
        trial_durations_ms,
    )

    cerebellum = concatenate_population_recordings(
        [nr.cerebellum for nr in neural_results],
        CerebellumPopulationsRecordings,
        trial_durations_ms,
    )

    cerebellum_handler = concatenate_population_recordings(
        [nr.cerebellum_handler for nr in neural_results],
        CerebellumHandlerPopulationsRecordings,
        trial_durations_ms,
    )

    weights = [nr.weights for nr in neural_results if nr.weights is not None]
    weights_result = weights if weights else None

    return NeuralResultManifest.model_construct(
        controller=controller,
        cerebellum=cerebellum,
        cerebellum_handler=cerebellum_handler,
        weights=weights_result,  # list[list[Path]] or None
        use_cerebellum=neural_results[0].use_cerebellum,
    )
