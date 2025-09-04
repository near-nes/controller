from typing import List, Tuple

import numpy as np
import structlog
from arm_1dof.bullet_arm_1dof import BulletArm1Dof
from arm_1dof.robot_arm_1dof import RobotArm1Dof
from config.plant_config import PlantConfig


class RoboticPlant:
    """
    Abstracts all PyBullet interactions for the 1-DOF robotic arm.
    Initializes the PyBullet environment, loads the robot, manages its state,
    applies commands, and implements plant reset functionality.
    """

    def __init__(self, config: PlantConfig, pybullet_instance):
        """
        Initializes the robotic plant.

        Args:
            config: The PlantConfig object containing all simulation parameters.
            pybullet_instance: The PyBullet instance (p).
            connect_gui: Whether to connect to the PyBullet GUI.
        """
        self.log = structlog.get_logger(type(self).__name__)
        self.log.info("Initializing RoboticPlant...")

        self.config: PlantConfig = config
        self.p = pybullet_instance

        # Initialize BulletArm1Dof helper
        self.bullet_world = BulletArm1Dof()

        if self.config.CONNECT_GUI:
            self.bullet_world.InitPybullet(bullet_connect=self.p.GUI)
        else:
            self.bullet_world.InitPybullet(bullet_connect=self.p.DIRECT)

        self.bullet_robot = self.bullet_world.LoadRobot()
        self.robot_id = self.bullet_robot._body_id
        self.is_locked_post = False
        self.is_locked_pre = False
        self.log.info("PyBullet initialized and robot loaded", robot_id=self.robot_id)

        # Specific joint ID for the 1-DOF arm
        self.elbow_joint_id: int = RobotArm1Dof.ELBOW_JOINT_ID

        # not sure if config should be "consumed" into properties or if should be kept as is
        self.initial_joint_position_rad: float = self.config.initial_joint_pos_rad
        self.target_joint_position_rad: float = self.config.target_joint_pos_rad

        self._test_init_tgt_positions()
        self.reset_plant()
        self.log.info(
            "RoboticPlant initialized and reset to initial state",
            initial_pos_rad=self.initial_joint_position_rad,
        )

    def _set_EE_pos(self, position_rad) -> np.ndarray:
        """Sets joint to position_rad and returns EE (cartesian) position"""
        self.p.resetJointState(
            self.bullet_robot._body_id,
            RobotArm1Dof.ELBOW_JOINT_ID,
            position_rad,
        )
        return self.p.getLinkState(
            self.bullet_robot._body_id, RobotArm1Dof.HAND_LINK_ID
        )[0]

    def _test_init_tgt_positions(self) -> None:
        self.init_hand_pos_ee = self._set_EE_pos(self.initial_joint_position_rad)
        self.trgt_hand_pos_ee = self._set_EE_pos(self.target_joint_position_rad)
        self.log.debug(
            "verified setting init and tgt and saved EE pos: ",
            init=self.init_hand_pos_ee,
            tgt=self.trgt_hand_pos_ee,
        )

    def set_gravity(self, enable: bool, magnitude: float = 9.81) -> None:
        """Enable or disable gravity in the simulation.

        Args:
            enable: If True, gravity is enabled with given magnitude
            magnitude: Gravity acceleration in m/s^2
        """
        if enable:
            self.p.setGravity(0, 0, -magnitude)
        else:
            self.p.setGravity(0, 0, 0)

    def update_stats(self) -> None:
        """Updates the underlying robot's statistics (e.g., joint states)."""
        self.bullet_robot.UpdateStats()

    def get_joint_state(self) -> Tuple[float, float]:
        """
        Gets the current state (position and velocity) of the elbow joint.

        Returns:
            A tuple (position_rad, velocity_rad_per_s).
        """
        pos = self.bullet_robot.JointPos(self.elbow_joint_id)
        vel = self.bullet_robot.JointVel(self.elbow_joint_id)
        return float(pos), float(vel)

    def get_ee_pose_and_velocity(self) -> Tuple[List[float], List[float]]:
        """
        Gets the current end-effector pose (x, y, z) and velocity (vx, vy, vz).
        The original code extracts [0:3] for pose and [0:3:2] for velocity (x,z components).
        We will return full 3D for now, and let consumer slice if needed.

        Returns:
            A tuple (pose_xyz_list, velocity_xyz_list).
        """
        # Original: pos[step, :] = bullet_robot.EEPose()[0][0:3]
        #           vel[step, :] = bullet_robot.EEVel()[0][0:3:2]
        # EEPose() returns [pos, orn, ...]
        ee_pose_full = self.bullet_robot.EEPose()
        # EEVel() returns [linearVel, angularVel, ...]
        ee_vel_full = self.bullet_robot.EEVel()

        pose_xyz = list(ee_pose_full[0])  # Linear part of pose
        linear_velocity_xyz = list(ee_vel_full[0])

        return pose_xyz, linear_velocity_xyz

    def set_joint_torques(self, torques: List[float]) -> None:
        """
        Applies the given torques to the elbow joint.

        Args:
            torques: A list containing the torque for the elbow joint.
                     Assumes a single value for the 1-DOF arm.
        """
        if len(torques) != 1:
            self.log.error(
                "Torques list must contain exactly one value for 1-DOF arm.",
                num_torques=len(torques),
            )
            raise ValueError(
                "Torques list must contain exactly one value for 1-DOF arm."
            )
        self.unlock_joint()
        self.is_locked_post = False
        self.is_locked_pre = False
        self.bullet_robot.SetJointTorques(
            joint_ids=[self.elbow_joint_id], torques=torques
        )

    def simulate_step(self, duration: float) -> None:
        """
        Steps the PyBullet simulation by the given duration.

        Args:
            duration: The time duration to simulate in seconds.
        """
        self.bullet_world.Simulate(sim_time=duration)

    def reset_plant(self) -> None:
        """
        Resets the robotic arm to its initial "zero" joint position and zero velocity.
        """
        self.p.resetJointState(
            bodyUniqueId=self.robot_id,
            jointIndex=self.elbow_joint_id,
            targetValue=self.initial_joint_position_rad,
            targetVelocity=0.0,
        )
        self.update_stats()
        self.log.debug(
            "Plant reset to initial position and zero velocity.",
            target_pos_rad=self.initial_joint_position_rad,
        )

    def lock_joint_post(self) -> None:
        """Lock joint at its current position using position control."""
        if not self.is_locked_post:
            self.log.debug("setting joint torque to zero")
            current_joint_pos_rad, vel = self.get_joint_state()
            self.log.debug("current joint state", pos=current_joint_pos_rad, vel=vel)

            # First reset state with zero velocity
            self.p.resetJointState(
                bodyUniqueId=self.robot_id,
                jointIndex=self.elbow_joint_id,
                targetValue=current_joint_pos_rad,
                targetVelocity=0.0,
            )
            self.log.debug(
                "Plant velocity locked.",
                target_pos_rad=self.initial_joint_position_rad,
                vel=vel,
            )

            self.p.setJointMotorControl2(
                bodyIndex=self.robot_id,
                jointIndex=self.elbow_joint_id,
                targetPosition=current_joint_pos_rad,
                controlMode=self.p.VELOCITY_CONTROL,
                targetVelocity=0.0,
                force=10000,  # whatever is strong enough to hold it
            )
            self.log.debug(
                "Joint locked at current position", pos=current_joint_pos_rad, vel=vel
            )
            self.is_locked_post = True

    def lock_joint_pre(self) -> None:
        """Lock joint at its initial position using position control."""
        if not self.is_locked_pre:
            self.log.debug("setting joint torque to zero")

            # First reset state with zero velocity
            self.p.resetJointState(
                bodyUniqueId=self.robot_id,
                jointIndex=self.elbow_joint_id,
                targetValue=self.initial_joint_position_rad,
                targetVelocity=0.0,
            )

            self.p.setJointMotorControl2(
                bodyIndex=self.robot_id,
                jointIndex=self.elbow_joint_id,
                targetPosition=self.initial_joint_position_rad,
                controlMode=self.p.VELOCITY_CONTROL,
                targetVelocity=0.0,
                force=10000,  # whatever is strong enough to hold it
            )
            self.is_locked_pre = True

    def unlock_joint(self) -> None:
        """Unlock joint by setting it to velocity control mode."""
        current_joint_pos_rad, vel = self.get_joint_state()
        self.p.setJointMotorControl2(
            bodyIndex=self.robot_id,
            jointIndex=self.elbow_joint_id,
            targetPosition=current_joint_pos_rad,
            controlMode=self.p.VELOCITY_CONTROL,
            force=0,
        )
