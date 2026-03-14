from enum import Enum

import numpy as np
from config.MasterParams import MasterParams
from config.core_models import SimulationParams


class TrialSection(Enum):
    (
        TIME_START,
        TIME_PREP,
        TIME_MOVE,
        TIME_LOCKED_WITH_FEEDBACK,
        TIME_GRASP,
        TIME_POST,
        TIME_END_TRIAL,
    ) = range(7)


PHASE_COLORS = {
    TrialSection.TIME_PREP: "#1A92F4",
    TrialSection.TIME_MOVE: "#42B046",
    TrialSection.TIME_LOCKED_WITH_FEEDBACK: "#FF9900",
    TrialSection.TIME_POST: "#7C432F",
}


def get_trial_phase_boundaries(sim_params: SimulationParams, trial_offset: float = 0):
    """Return list of (start_ms, end_ms, section, color) for each phase in one trial."""
    t = trial_offset
    phases = []
    for section, dur in [
        (TrialSection.TIME_PREP, sim_params.time_prep),
        (TrialSection.TIME_MOVE, sim_params.time_move),
        (TrialSection.TIME_LOCKED_WITH_FEEDBACK, sim_params.time_locked_with_feedback),
        (TrialSection.TIME_POST, sim_params.time_grasp + sim_params.time_post),
    ]:
        color = PHASE_COLORS[section]
        phases.append((t, t + dur, section, color))
        t += dur
    return phases


def draw_trial_phases(
    axes,
    sim_params: SimulationParams,
    num_trials: int = 1,
    alpha: float = 0.2,
    time_unit_s: bool = False,
):
    """Draw vertical lines and light shading for trial phase boundaries on given axes."""
    if not isinstance(axes, (list, np.ndarray)):
        axes = [axes]

    trial_dur = sim_params.duration_ms
    scale = 1 / 1000 if time_unit_s else 1
    for trial_idx in range(num_trials):
        phases = get_trial_phase_boundaries(
            sim_params, trial_offset=trial_idx * trial_dur
        )
        for start, end, label, color in phases:
            for ax in axes:
                ax.axvspan(start * scale, end * scale, alpha=alpha, color=color, zorder=0)
                ax.axvline(
                    start * scale, color=color, linestyle="--", linewidth=0.1, alpha=1, zorder=1
                )


def get_current_section(curr_time_ms: float, mp: MasterParams):
    if curr_time_ms == 0:
        return TrialSection.TIME_START
    elif curr_time_ms <= mp.simulation.time_prep:
        return TrialSection.TIME_PREP
    elif curr_time_ms <= (mp.simulation.time_move + mp.simulation.time_prep):
        return TrialSection.TIME_MOVE
    elif curr_time_ms <= (
        mp.simulation.time_move
        + mp.simulation.time_prep
        + mp.simulation.time_locked_with_feedback
    ):
        return TrialSection.TIME_LOCKED_WITH_FEEDBACK
    elif curr_time_ms <= (
        mp.simulation.time_move
        + mp.simulation.time_prep
        + mp.simulation.time_locked_with_feedback
        + mp.simulation.time_grasp
    ):
        return TrialSection.TIME_GRASP
    elif 0 <= (curr_time_ms - mp.simulation.duration_ms) < mp.simulation.resolution:
        return TrialSection.TIME_END_TRIAL
    else:
        return TrialSection.TIME_POST
