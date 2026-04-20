# minjerk-dynamics

Minimum-jerk trajectory generation and 1-DOF inverse dynamics.

This is a custom package developed for [Task T3.4 of the Neurorobotics EBRAINS 2.0 work package](https://wiki.ebrains.eu/bin/view/Collabs/closed-loop-motor-t3-4/). It is used in three components of the neurocontroller:

- **Mocked planner**: generates smooth minimum-jerk reference trajectories for the robot to follow.
- **GLE-based planner**: trains a neural planner using minimum-jerk trajectories as targets.
- **E-prop motor cortex**: trains an M1 network (using the mocked planner) with inverse-dynamics motor commands as targets.

## What it does

- **Minimum-jerk trajectories**: 5th-order polynomials for smooth point-to-point movement, with support for padded prep/post phases and M1 delay shifting.
- **Motor commands**: computes joint torques via inverse dynamics (`torques = I * acc + gravity`) from the generated trajectory.

## Usage

```python
from minjerk_dynamics.trajectory import generate_trajectory, generate_motor_commands
from minjerk_dynamics.dynamics import inverse_dynamics_1dof

# Trajectory (angles in radians, times in milliseconds)
traj = generate_trajectory(
    init_angle_rad=0.0,
    target_angle_rad=1.0,
    resolution_ms=1.0,
    time_prep_ms=500.0,
    time_move_ms=1000.0,
    time_locked_with_feedback_ms=500.0,
    time_post_ms=200.0,
    m1_delay_ms=50.0,
)

# Motor commands (torques)
torques = generate_motor_commands(
    init_angle_rad=0.0,
    target_angle_rad=1.0,
    resolution_ms=1.0,
    time_prep_ms=500.0,
    time_move_ms=1000.0,
    time_locked_with_feedback_ms=500.0,
    time_post_ms=200.0,
    inertia=0.02,
)
```

## Installation

```
pip install minjerk-dynamics
```

Only dependency is numpy. Requires Python >= 3.10.
