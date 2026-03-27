from ntpath import join
import numpy as np
from pandas import array
import pybullet

class RobotArm1Dof:
    """Sekeleton arm bullet body"""
    UPPER_ARM_LINK_ID=1
    FOREARM_LINK_ID=2
    HAND_LINK_ID=3

    SHOULDER_A_JOINT_ID=0
    ELBOW_JOINT_ID=1

    def __init__(self, bullet_ctrl, bullet_body_id) -> None:

        self._bullet_ctrl = bullet_ctrl
        self._body_id = bullet_body_id
        pybullet.resetBasePositionAndOrientation(
            bodyUniqueId=self._body_id, 
            posObj=[0., 0., 0.], ornObj=[0., 0., 0., 1.], 
            physicsClientId=self._bullet_ctrl.server_id)
        
        # Set mass
        dyn_info = pybullet.getDynamicsInfo(self._body_id, RobotArm1Dof.UPPER_ARM_LINK_ID, \
            physicsClientId=self._bullet_ctrl.server_id)
        self._upper_arm_mass = dyn_info[0]

        dyn_info = pybullet.getDynamicsInfo(self._body_id, RobotArm1Dof.FOREARM_LINK_ID, \
            physicsClientId=self._bullet_ctrl.server_id)
        self._lower_arm_mass = dyn_info[1]

        # Disable position and velocity based joint motor controls
        pybullet.setJointMotorControlArray(self._body_id, jointIndices=[RobotArm1Dof.SHOULDER_A_JOINT_ID, RobotArm1Dof.ELBOW_JOINT_ID], \
            controlMode=pybullet.POSITION_CONTROL, forces=[0.0, 0.0], \
            physicsClientId=self._bullet_ctrl.server_id)

        pybullet.setJointMotorControlArray(self._body_id, jointIndices=[RobotArm1Dof.SHOULDER_A_JOINT_ID, RobotArm1Dof.ELBOW_JOINT_ID], \
            controlMode=pybullet.VELOCITY_CONTROL, forces=[0.0, 0.0], \
            physicsClientId=self._bullet_ctrl.server_id)

        # Initialize joint/link state storage
        self._joint_stats = {}
        self._ee_link_state = None

        self.UpdateStats()

    def UpdateStats(self):
        """Query state info from bullet"""
        # Retrieve joint info
        self._joint_stats[RobotArm1Dof.SHOULDER_A_JOINT_ID] = pybullet.getJointState(self._body_id, RobotArm1Dof.SHOULDER_A_JOINT_ID, \
            physicsClientId=self._bullet_ctrl.server_id)

        self._joint_stats[RobotArm1Dof.ELBOW_JOINT_ID] = pybullet.getJointState(self._body_id, RobotArm1Dof.ELBOW_JOINT_ID, \
            physicsClientId=self._bullet_ctrl.server_id)

        self._ee_link_state = pybullet.getLinkState(self._body_id, RobotArm1Dof.HAND_LINK_ID, \
            computeLinkVelocity=True,
            physicsClientId=self._bullet_ctrl.server_id)

    def JointPos(self, joint_id) -> float:
        """Get joint info"""
        return self._joint_stats[joint_id][0]

    def JointVel(self, joint_id) -> float:
        """Get joint info"""
        return self._joint_stats[joint_id][1]

    def EEPose(self) -> tuple:
        """Get end effector pose, linear pos and rotation (as quaternion)"""
        return (self._ee_link_state[0], self._ee_link_state[1])

    def EEVel(self) -> tuple:
        """Get end effector vel, linear and angular"""
        return (self._ee_link_state[6], self._ee_link_state[7])

    def SetJointTorques(self, joint_ids, torques) -> None:
        """Sets torques applied to specified joints."""
        pybullet.setJointMotorControlArray(self._body_id, jointIndices=joint_ids, \
            controlMode=pybullet.TORQUE_CONTROL, forces=torques, \
            physicsClientId=self._bullet_ctrl.server_id)