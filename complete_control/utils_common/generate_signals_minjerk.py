"""Thin wrappers around minjerk_dynamics for use with SimulationParams."""

from minjerk_dynamics import generate_motor_commands, generate_trajectory

from complete_control.config.core_models import SimulationParams


def generate_trajectory_minjerk(sim: SimulationParams, m1_delay: float = 0.0):
    """Generate trajectory for the simulation.

    The trajectory is shifted earlier by m1_delay so that the planner feeds M1
    during the end of prep, giving it time to process before TIME_MOVE starts.

    Returns:
        np.ndarray: Trajectory array for the simulation
    """
    return generate_trajectory(
        init_angle_rad=sim.oracle.init_pos_angle_rad,
        target_angle_rad=sim.oracle.tgt_pos_angle_rad,
        resolution_ms=sim.resolution,
        time_prep_ms=sim.time_prep,
        time_move_ms=sim.time_move,
        time_locked_with_feedback_ms=sim.time_locked_with_feedback,
        time_post_ms=sim.time_grasp + sim.time_post,
        m1_delay_ms=m1_delay,
    )


def generate_motor_commands_minjerk(sim: SimulationParams):
    """Generate motor commands for the simulation.

    Returns:
        np.ndarray: Motor commands array for the simulation
    """
    robot = sim.oracle.robot_spec
    return generate_motor_commands(
        init_angle_rad=sim.oracle.init_pos_angle_rad,
        target_angle_rad=sim.oracle.tgt_pos_angle_rad,
        resolution_ms=sim.resolution,
        time_prep_ms=sim.time_prep,
        time_move_ms=sim.time_move,
        time_locked_with_feedback_ms=sim.time_locked_with_feedback,
        time_post_ms=sim.time_grasp + sim.time_post,
        inertia=robot.I[0],
    )


def generate_signals(sim: SimulationParams):
    return generate_trajectory_minjerk(sim), generate_motor_commands_minjerk(sim)


if __name__ == "__main__":
    sim_p = SimulationParams()
    trj, motorCommands = generate_signals(sim_p)
    print(f"Generated trajectory shape: {trj.shape}")
    print(trj)
    print(f"Generated motor commands shape: {motorCommands.shape}")
    print(motorCommands)
    print(f"Expected length: {sim_p.duration_ms / sim_p.resolution}")
