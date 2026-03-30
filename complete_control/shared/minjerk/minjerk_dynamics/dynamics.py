import numpy as np


def inverse_dynamics_1dof(
    inertia: float,
    pos: np.ndarray,
    vel: np.ndarray,
    acc: np.ndarray,
    g: float = 0.0,
    mass: float = 0.0,
    link_length: float = 0.0,
) -> np.ndarray:
    """Compute joint torques from kinematics for a 1-DOF arm.

    torques = I * acc + g * m * L/2 * sin(pos)

    When g=0 (the default, matching the current controller config),
    this reduces to torques = I * acc.
    """
    torques = inertia * acc + g * mass * link_length / 2 * np.sin(pos)
    return torques
