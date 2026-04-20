from typing import List, Tuple

import structlog

_log = structlog.get_logger(__name__)


def compute_spike_rate(
    spikes: List[Tuple[float, int]],  # List of (timestamp, channel_id)
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

    duration = time_end - time_start

    if duration <= 0 or n_neurons <= 0:
        # Avoid division by zero or meaningless rates
        _log.warning(
            "Invalid duration or n_neurons for rate calculation",
            duration=duration,
            n_neurons=n_neurons,
        )
        return 0.0, int(count)

    rate_hz = count / (duration * n_neurons)
    return rate_hz, count
