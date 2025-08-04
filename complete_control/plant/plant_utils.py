from typing import List, Tuple

import numpy as np
import structlog
from pydantic import BaseModel
from utils_common.custom_types import NdArray

_log = structlog.get_logger(__name__)


class JointData(BaseModel):
    """Holds time-series data for a single joint."""

    pos_rad: NdArray
    vel_rad_s: NdArray
    pos_ee_m: NdArray
    vel_ee_m_s: NdArray
    spk_rate_pos_hz: NdArray
    spk_rate_neg_hz: NdArray
    spk_rate_net_hz: NdArray
    input_cmd_torque: NdArray
    input_cmd_total_torque: NdArray

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def empty(cls, num_total_steps: int):
        return cls(
            pos_rad=np.zeros(num_total_steps),
            vel_rad_s=np.zeros(num_total_steps),
            pos_ee_m=np.zeros([num_total_steps, 3]),
            vel_ee_m_s=np.zeros([num_total_steps, 2]),
            spk_rate_pos_hz=np.zeros(num_total_steps),
            spk_rate_neg_hz=np.zeros(num_total_steps),
            spk_rate_net_hz=np.zeros(num_total_steps),
            input_cmd_torque=np.zeros(num_total_steps),
            input_cmd_total_torque=np.zeros(num_total_steps),
        )

    def record_step(
        self,
        step: int,
        joint_pos_rad: float,
        joint_vel_rad_s: float,
        ee_pos_m: List[float],
        ee_vel_m_s: List[float],
        spk_rate_pos_hz: float,
        spk_rate_neg_hz: float,
        spk_rate_net_hz: float,
        input_cmd_torque: float,
    ):
        """Records data for the current simulation step."""
        if step < 0 or step >= self.pos_rad.shape[0]:
            _log.error(
                "Step index out of bounds for data recording",
                step=step,
                max_steps=self.pos_rad.shape[0],
            )
            return

        self.pos_rad[step] = joint_pos_rad
        self.vel_rad_s[step] = joint_vel_rad_s
        self.pos_ee_m[step, :] = ee_pos_m[0:3]

        if len(ee_vel_m_s) == 3:
            self.vel_ee_m_s[step, :] = [ee_vel_m_s[0], ee_vel_m_s[2]]
        elif len(ee_vel_m_s) == 2:
            self.vel_ee_m_s[step, :] = ee_vel_m_s
        else:
            _log.error("Unexpected ee_vel_m_s length", length=len(ee_vel_m_s))
            raise ValueError("Unexpected ee_vel_m_s length")

        self.spk_rate_pos_hz[step] = spk_rate_pos_hz
        self.spk_rate_neg_hz[step] = spk_rate_neg_hz
        self.spk_rate_net_hz[step] = spk_rate_net_hz
        self.input_cmd_torque[step] = input_cmd_torque
        self.input_cmd_total_torque[step] = input_cmd_torque


def compute_spike_rate(
    spikes: List[Tuple[float, int]],  # List of (timestamp, channel_id)
    weight: float,
    n_neurons: int,
    time_start: float,
    time_end: float,
) -> Tuple[float, int]:
    """
    Computes spike rate within a given time window.

    Args:
        spikes: List of spikes, where each spike is (timestamp, channel_id).
        weight: Weight associated with spikes (from original code, seems to be w).
        n_neurons: Number of neurons in the population.
        time_start: Start of the time buffer for rate calculation.
        time_end: End of the time buffer for rate calculation.

    Returns:
        A tuple (spike_rate_hz, weighted_spike_count).
    """
    if not spikes:
        return 0.0, 0

    # Filter spikes within the time window [time_start, time_end)
    # Using a more direct iteration for potentially better performance with many spikes
    # than converting to numpy array first for just filtering.
    count = 0
    for t, _ in spikes:
        if time_start <= t < time_end:
            count += 1

    weighted_count = weight * count
    duration = time_end - time_start

    if duration <= 0 or n_neurons <= 0:
        # Avoid division by zero or meaningless rates
        _log.warning(
            "Invalid duration or n_neurons for rate calculation",
            duration=duration,
            n_neurons=n_neurons,
        )
        return 0.0, int(weighted_count)

    rate_hz = weighted_count / (duration * n_neurons)
    return rate_hz, int(weighted_count)
