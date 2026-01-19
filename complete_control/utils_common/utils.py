from enum import Enum

from config.MasterParams import MasterParams


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
