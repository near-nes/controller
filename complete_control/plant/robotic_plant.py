import math
from pathlib import Path
from typing import List, Tuple

import numpy as np
import structlog
from bullet_muscle_sim.arm_1dof.bullet_arm_1dof import BulletArm1Dof
from bullet_muscle_sim.arm_1dof.robot_arm_1dof import RobotArm1Dof
from config.plant_config import PlantConfig
from plant.plant_models import JointState, JointStates


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
        self.bullet_world = BulletArm1Dof(self.p)

        if self.config.CONNECT_GUI:
            self.bullet_world.InitPybullet(bullet_connect=self.p.GUI)
        else:
            self.bullet_world.InitPybullet(bullet_connect=self.p.DIRECT)

        self.bullet_robot = self.bullet_world.LoadRobot()
        self.robot_id = self.bullet_robot._body_id
        self.shoulder_joint_id = self.bullet_robot.SHOULDER_A_JOINT_ID
        self.hand_joint_id = (
            self.bullet_robot.HAND_LINK_ID
        )  # TODO this only works because the link id of the hand is the same as the joint id of the knuckles. fix it!
        self.elbow_joint_locked = False
        self.ball = None
        self.bullet_world.LoadPlane()
        self.ball_hand_rel_pos = self.ball_hand_rel_orn = None

        self.target_position = self._set_rad_elbow(
            config.target_joint_pos_rad
            + config.master_config.simulation.oracle.tgt_visual_offset_rad
        )
        self.reset_target()
        self.shoulder_joint_start_position_rad = 0
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

    def _set_rad_elbow(self, position_rad) -> np.ndarray:
        """Sets joint to position_rad and returns EE (cartesian) position"""
        self.p.resetJointState(
            self.bullet_robot._body_id,
            RobotArm1Dof.ELBOW_JOINT_ID,
            position_rad,
        )
        return self.p.getLinkState(
            self.bullet_robot._body_id, RobotArm1Dof.HAND_LINK_ID
        )[0]

    def _set_pos_all_joints(self, state: JointStates):
        self.p.resetJointState(
            self.bullet_robot._body_id,
            self.shoulder_joint_id,
            state.shoulder.pos,
        )
        self.p.resetJointState(
            self.bullet_robot._body_id,
            self.elbow_joint_id,
            state.elbow.pos,
        )
        self.p.resetJointState(
            self.bullet_robot._body_id,
            self.hand_joint_id,
            state.hand.pos,
        )

    def _set_rad_shoulder(self, position_rad) -> np.ndarray:
        """Sets joint to position_rad and returns EE (cartesian) position"""
        self.p.resetJointState(
            self.bullet_robot._body_id,
            RobotArm1Dof.SHOULDER_A_JOINT_ID,
            position_rad,
        )
        return self.p.getLinkState(
            self.bullet_robot._body_id, RobotArm1Dof.SHOULDER_A_JOINT_ID
        )[0]

    def _capture_state_and_save(self, image_path: Path, axis="y") -> None:
        from PIL import Image

        self.log.debug("setting up camera...")

        camera_target_position = [0.3, 0.3, 1.5]
        camera_position = [0, -1, 1.7]
        up_vector = [0, 0, 1]
        width = 1024
        height = 768
        fov = 60
        aspect = width / height
        near = 0.1
        far = 100
        projection_matrix = self.p.computeProjectionMatrixFOV(fov, aspect, near, far)
        view_matrix = self.p.computeViewMatrix(
            camera_position, camera_target_position, up_vector
        )
        self.log.debug("getting image...")
        img_arr = self.p.getCameraImage(
            width,
            height,
            viewMatrix=view_matrix,
            projectionMatrix=projection_matrix,
            renderer=self.p.ER_BULLET_HARDWARE_OPENGL,
        )

        self.log.debug("saving image...")
        rgb_buffer = np.array(img_arr[2])
        rgb = rgb_buffer[:, :, :3]  # drop alpha
        Image.fromarray(rgb.astype(np.uint8)).save(image_path)
        self.log.info(f"saved input image at {str(image_path)}")

    def _test_init_tgt_positions(self) -> None:
        self.init_hand_pos_ee = self._set_rad_elbow(self.initial_joint_position_rad)
        self.trgt_hand_pos_ee = self._set_rad_elbow(self.target_joint_position_rad)
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

    def get_joint_states(self) -> JointStates:
        """
        Gets the current state (position and velocity) all joints.
        """
        s = self.p.getJointState(
            bodyUniqueId=self.robot_id, jointIndex=self.shoulder_joint_id
        )
        e = self.p.getJointState(
            bodyUniqueId=self.robot_id, jointIndex=self.elbow_joint_id
        )
        h = self.p.getJointState(
            bodyUniqueId=self.robot_id, jointIndex=self.hand_joint_id
        )
        return JointStates(
            shoulder=JointState(s[0], s[1]),
            elbow=JointState(e[0], e[1]),
            hand=JointState(h[0], h[1]),
        )

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

    def set_elbow_joint_torque(self, torques: List[float]) -> None:
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
        self.p.resetJointState(
            bodyUniqueId=self.robot_id,
            jointIndex=self.shoulder_joint_id,
            targetValue=self.shoulder_joint_start_position_rad,
            targetVelocity=0.0,
        )
        self.p.setJointMotorControl2(
            self.bullet_robot._body_id,
            self.bullet_robot.SHOULDER_A_JOINT_ID,
            controlMode=self.p.VELOCITY_CONTROL,
            targetVelocity=0,
        )
        self.p.resetJointState(
            bodyUniqueId=self.robot_id,
            jointIndex=self.bullet_robot.HAND_LINK_ID,
            targetValue=0,
            targetVelocity=0.0,
        )
        move_hand = self.p.setJointMotorControl2(
            self.bullet_robot._body_id,
            self.bullet_robot.HAND_LINK_ID,
            controlMode=self.p.VELOCITY_CONTROL,
            targetVelocity=0,
        )
        self.update_stats()
        self.log.debug(
            "Plant reset to initial position and zero velocity.",
            target_pos_rad=self.initial_joint_position_rad,
        )

    def reset_target(self) -> None:
        if self.ball:
            self.p.removeBody(self.ball)
        self.ball = self.bullet_world.LoadTarget(
            self.target_position,
            self.config.master_config.simulation.oracle.target_color.value,
        )

    def lock_elbow_joint(self) -> None:
        """Lock elbow joint at its current position using position control."""
        if not self.elbow_joint_locked:
            self.log.debug("setting joint torque to zero")
            current_joint_pos_rad, vel = self.get_joint_states().elbow
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
            self.elbow_joint_locked = True

    def unlock_joint(self) -> None:
        """Unlock joint by setting it to velocity control mode."""
        current_joint_pos_rad, vel = self.get_joint_states().elbow
        self.p.setJointMotorControl2(
            bodyIndex=self.robot_id,
            jointIndex=self.elbow_joint_id,
            targetPosition=current_joint_pos_rad,
            controlMode=self.p.VELOCITY_CONTROL,
            force=0,
        )
        self.elbow_joint_locked = False

    def check_target_proximity(self) -> bool:
        body_id = self.bullet_robot._body_id
        elbow_state = self.p.getJointState(body_id, 1)[0]
        return math.isclose(
            elbow_state,
            self.target_joint_position_rad,
            abs_tol=np.deg2rad(
                self.config.master_config.simulation.oracle.target_tolerance_angle_deg
            ),
        )

    def grasp(self) -> None:
        move_hand = self.p.setJointMotorControl2(
            self.bullet_robot._body_id,
            self.bullet_robot.HAND_LINK_ID,
            controlMode=self.p.VELOCITY_CONTROL,
            targetVelocity=0.2,
        )

    def move_shoulder(self, speed: float) -> None:
        move = self.p.setJointMotorControl2(
            self.bullet_robot._body_id,
            self.bullet_robot.SHOULDER_A_JOINT_ID,
            controlMode=self.p.VELOCITY_CONTROL,
            targetVelocity=speed,
        )
        move_hand = self.p.setJointMotorControl2(
            self.bullet_robot._body_id,
            self.bullet_robot.HAND_LINK_ID,
            controlMode=self.p.VELOCITY_CONTROL,
            targetVelocity=0,
        )

    def update_ball_position(self):
        if self.ball_hand_rel_pos is None or self.ball_hand_rel_orn is None:
            # assume that we want to maintain the relative pos/orient of the first
            # time update_ball_position is called for all subsequent calls
            hand_state = self.p.getLinkState(
                self.bullet_robot._body_id, self.bullet_robot.FOREARM_LINK_ID
            )
            hand_pos, hand_orn = hand_state[0], hand_state[1]
            inv_hand_pos, inv_hand_orn = self.p.invertTransform(hand_pos, hand_orn)
            ball_pos, ball_orn = self.p.getBasePositionAndOrientation(self.ball)
            self.ball_hand_rel_pos, self.ball_hand_rel_orn = self.p.multiplyTransforms(
                inv_hand_pos, inv_hand_orn, ball_pos, ball_orn
            )

        hand_state = self.p.getLinkState(
            self.bullet_robot._body_id, self.bullet_robot.FOREARM_LINK_ID
        )
        hand_pos, hand_orn = hand_state[0], hand_state[1]
        ball_pos, ball_orn = self.p.multiplyTransforms(
            hand_pos, hand_orn, self.ball_hand_rel_pos, self.ball_hand_rel_orn
        )
        self.p.resetBasePositionAndOrientation(self.ball, ball_pos, ball_orn)
