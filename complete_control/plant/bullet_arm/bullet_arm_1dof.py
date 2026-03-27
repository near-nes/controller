import os
from pathlib import Path

import numpy as np

from . import robot_arm_1dof

_DEFAULT_SDF_MODELS_DIR = str(Path(__file__).resolve().parent.parent / "sdf_models")


class BulletArm1Dof:
    """Class to initialize pybullet server and load robot"""

    SDF_MODELS_SUBDIR = "arm_1dof"
    SDF_SEARCH_PATH = "/".join(
        [os.environ.get("SDF_MODELS_DIR", _DEFAULT_SDF_MODELS_DIR), SDF_MODELS_SUBDIR]
    )
    SDF_MODEL_NAME = "demo_human_col"
    SDF_MODEL_FILENAME = "/".join([SDF_MODEL_NAME, "skeleton.sdf"])
    URDF_MODEL_FILENAME = "/".join([SDF_MODEL_NAME, "skeleton.urdf"])
    PLANE_MODEL_FILENAME = "/".join([SDF_MODEL_NAME, "plane.urdf"])

    def __init__(self, pybullet_instance=None) -> None:
        if pybullet_instance is None:
            import pybullet as p

            pybullet_instance = p
        self._server_id = -1
        self._skel_arm = None
        self._skel_arm_id = -1
        self._skel_muscles = None
        self.p = pybullet_instance

    @property
    def server_id(self):
        """Pybullet server ID"""
        return self._server_id

    def InitPybullet(
        self,
        bullet_connect,
        g=[0.0, 0.0, 0.0],
        sdf_search_path=SDF_SEARCH_PATH,
    ) -> None:
        """Start bullet server and set sdf search path"""
        # Connect to pybullet
        self._server_id = self.p.connect(bullet_connect)

        self.p.setGravity(g[0], g[1], g[2], physicsClientId=self._server_id)
        self.p.setAdditionalSearchPath(
            path=sdf_search_path, physicsClientId=self._server_id
        )

        self._timestep = self.p.getPhysicsEngineParameters(
            physicsClientId=self._server_id
        )["fixedTimeStep"]

    def LoadPlane(self, robot_sdf_filename=PLANE_MODEL_FILENAME):
        """Load plane from sdf file"""
        plane_id = self.p.loadURDF(
            fileName=robot_sdf_filename,
            useFixedBase=True,
            physicsClientId=self._server_id,
        )
        # Define new position (x, y, z)
        new_position = [0, 10, 10]  # Change as needed

        # Create rotation quaternion for 90 degrees around Z-axis
        # For other axes: X-axis = [1,0,0], Y-axis = [0,1,0], Z-axis = [0,0,1]
        rotation_quaternion = self.p.getQuaternionFromEuler(
            [np.pi / 2, 0, 0]
        )  # 90 deg around Z

        # Apply the transformation
        self.p.resetBasePositionAndOrientation(
            plane_id, new_position, rotation_quaternion, physicsClientId=self._server_id
        )

        self._plane = plane_id
        return self._plane

    def LoadRobot(
        self, robot_sdf_filename=URDF_MODEL_FILENAME
    ) -> robot_arm_1dof.RobotArm1Dof:
        """Load robot from sdf file"""
        self._skel_arm_id = self.p.loadURDF(
            fileName=robot_sdf_filename,
            useFixedBase=True,
            physicsClientId=self._server_id,
        )

        self._skel_arm = robot_arm_1dof.RobotArm1Dof(
            bullet_ctrl=self, bullet_body_id=self._skel_arm_id
        )

        return self._skel_arm

    def LoadTarget(self, target_position, target_color=[1, 0, 0, 1]):
        ball_shape = self.p.createVisualShape(
            shapeType=self.p.GEOM_SPHERE,
            radius=0.02,
            rgbaColor=target_color,
            physicsClientId=self._server_id,
        )
        # ball_collision = self.p.createCollisionShape(
        #     shapeType=self.p.GEOM_SPHERE,
        #     radius=0.02,
        #     physicsClientId=self._server_id,
        # )
        ball = self.p.createMultiBody(
            baseMass=0,
            baseInertialFramePosition=[0, 0, 0],
            baseCollisionShapeIndex=-1,
            baseVisualShapeIndex=ball_shape,
            basePosition=target_position,
            physicsClientId=self._server_id,
        )
        # ball_const = self.p.createConstraint(
        #     self._skel_arm_id,
        #     4,
        #     ball,
        #     -1,
        #     self.p.JOINT_FIXED,
        #     [0, 0, 0],
        #     self.p.getJointState(self._skel_arm_id, 4)[:2],
        #     [0, 0, 0],
        #     [0, 0, 0],
        #     [0, 0, 0],
        #     physicsClientId=self._server_id,
        # )
        return ball
        # return ball, ball_const

    def Simulate(self, sim_time) -> None:
        t = 0
        while t < sim_time:
            self.p.stepSimulation(physicsClientId=self._server_id)

            t += self._timestep
