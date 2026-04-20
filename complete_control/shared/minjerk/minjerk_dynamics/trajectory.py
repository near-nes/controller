"""Minimum-jerk trajectory generation and motor command computation

All angles are in radians, all times in milliseconds unless noted otherwise.
"""

import numpy as np

from .dynamics import inverse_dynamics_1dof


def minimum_jerk(
    x_init: np.ndarray, x_des: np.ndarray, timespan: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """5th-order minimum-jerk polynomial.

    Returns (trajectory, polynomial_coefficients).
    """
    T_max = timespan[-1]
    tmspn = timespan.reshape(timespan.size, 1)

    a = 6 * (x_des - x_init) / np.power(T_max, 5)
    b = -15 * (x_des - x_init) / np.power(T_max, 4)
    c = 10 * (x_des - x_init) / np.power(T_max, 3)
    d = np.zeros(x_init.shape)
    e = np.zeros(x_init.shape)
    g = x_init

    pol = np.array([a, b, c, d, e, g])
    pp = a * np.power(tmspn, 5) + b * np.power(tmspn, 4) + c * np.power(tmspn, 3) + g

    return pp, pol


def minimum_jerk_ddt(
    x_init: np.ndarray, x_des: np.ndarray, timespan: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Second derivative (acceleration) of the minimum-jerk polynomial."""
    T_max = timespan[-1]
    tmspn = timespan.reshape(timespan.size, 1)

    a = 120 * (x_des - x_init) / np.power(T_max, 5)
    b = -180 * (x_des - x_init) / np.power(T_max, 4)
    c = 60 * (x_des - x_init) / np.power(T_max, 3)
    d = np.zeros(x_init.shape)

    pol = np.array([a, b, c, d])
    pp = a * np.power(tmspn, 3) + b * np.power(tmspn, 2) + c * np.power(tmspn, 1) + d
    return pp, pol


def generate_trajectory(
    init_angle_rad: float,
    target_angle_rad: float,
    resolution_ms: float,
    time_prep_ms: float,
    time_move_ms: float,
    time_locked_with_feedback_ms: float,
    time_post_ms: float,
    m1_delay_ms: float = 0.0,
) -> np.ndarray:
    """Generate a padded minimum-jerk trajectory.

    The trajectory is shifted earlier by ``m1_delay_ms`` so that the planner
    feeds M1 during the end of prep, giving it time to process before movement.

    ``time_post_ms`` should include any grasp phase: it is the total duration
    after locked-with-feedback where the output is zeroed.
    """
    time_prep = time_prep_ms - m1_delay_ms
    time_sim_vec = np.linspace(
        0, time_move_ms, num=int(np.round(time_move_ms / resolution_ms)), endpoint=True
    )

    init_pos = np.array([init_angle_rad])
    tgt_pos = np.array([target_angle_rad])

    trj, _ = minimum_jerk(init_pos, tgt_pos, time_sim_vec)

    trj_prep = trj[0] * np.ones(int(time_prep / resolution_ms))
    trj_locked = trj[-1] * np.ones(
        int((time_locked_with_feedback_ms + m1_delay_ms) / resolution_ms)
    )
    trj_post = np.zeros(int(time_post_ms / resolution_ms))
    trj = np.concatenate((trj_prep, trj.flatten(), trj_locked, trj_post))

    return trj


def generate_motor_commands(
    init_angle_rad: float,
    target_angle_rad: float,
    resolution_ms: float,
    time_prep_ms: float,
    time_move_ms: float,
    time_locked_with_feedback_ms: float,
    time_post_ms: float,
    inertia: float,
    g: float = 0.0,
    mass: float = 0.0,
    link_length: float = 0.0,
) -> np.ndarray:
    """Generate motor commands (torques) via inverse dynamics of a min-jerk trajectory.

    ``time_post_ms`` should include any grasp phase — it is the total duration
    after locked-with-feedback where the output is zeroed.
    """
    n_steps = int(np.round(time_move_ms / resolution_ms))
    # Work in seconds for dynamics
    time_vec_s = np.linspace(0, time_move_ms / 1e3, num=n_steps, endpoint=True)

    init_pos = np.array([init_angle_rad])
    tgt_pos = np.array([target_angle_rad])

    pos, _ = minimum_jerk(init_pos, tgt_pos, time_vec_s)
    dt = time_vec_s[1] - time_vec_s[0]
    vel = np.gradient(pos, dt, axis=0)
    acc, _ = minimum_jerk_ddt(init_pos, tgt_pos, time_vec_s)

    mcmd = inverse_dynamics_1dof(
        inertia, pos, vel, acc, g=g, mass=mass, link_length=link_length
    )

    mc_prep = np.zeros(int(time_prep_ms / resolution_ms))
    mc_post = np.zeros(
        int((time_locked_with_feedback_ms + time_post_ms) / resolution_ms)
    )
    return np.concatenate((mc_prep, mcmd.flatten(), mc_post))
