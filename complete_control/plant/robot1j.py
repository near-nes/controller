"""robot one joint class"""

__authors__ = "Benedetta Gambosi"
__copyright__ = "Copyright 2022"
__credits__ = ["Benedetta Gambosi"]
__license__ = "GPL"
__version__ = "1.0.1"

import numpy as np
from config.core_models import RobotSpecParams

from .body import Body

g = 0  # -9.81


class Robot1J(Body):

    def __init__(
        self,
        IC_pos=np.array([0.0]),
        IC_vel=np.array([0.0]),
        robot: RobotSpecParams = RobotSpecParams(),
    ):

        if IC_pos.shape != IC_vel.shape:
            raise Exception("Position and velocity need to have the same format")

        self.robot = dict()
        self.robot["mass"] = np.array(robot.mass)
        self.robot["links"] = np.array(robot.links)
        self.robot["I"] = np.array(robot.I)
        self.pos = IC_pos
        self.vel = IC_vel
        self.I = self.robot["I"]  # mass *link**2

    @property
    def mass(self):
        return self.robot["mass"]

    @property
    def links(self):
        return self.robot["links"]

    @property
    def I(self):
        return self.robot["I"]

    # State variable setter
    @mass.setter
    def mass(self, value):
        self.robot["mass"] = value

    @links.setter
    def links(self, value):
        self.robot["links"] = value

    @I.setter
    def I(self, value):
        self.robot["I"] = value

    # Integrate the body over dt
    def integrateTimeStep(self, u, dt):
        # if u.shape!=self._angles.shape or u.shape!=self._ang_vel.shape:
        #     raise Exception("Wrong format")

        self._acc = (
            u - g * self.robot["mass"] * self.robot["links"] / 2 * np.sin(self._pos)
        ) / self.I
        self._vel = self._vel + self._acc * dt
        # self._vel = self._vel + u/self.robot["links"]**2 * dt
        self._pos = self._pos + self._vel * dt

    # Definition of the inverse kinematic given end-effector position
    def inverseKin(self, pos_external):
        # positions, velocities and accelerations are expected to be N-by-nV arrays,
        # where N is the number of timesteps and nV is the number of variables
        # if pos_external.ndim>1:
        #    if pos_external.shape[1]!=self._angles.shape[0]:
        #         raise Exception("Wrong value format")
        # elif pos_external.shape!=self._angles.shape:
        #    raise Exception("Wrong value format")
        theta = []
        for i in range(pos_external.shape[0]):
            if pos_external[i, 0] == 0.0:
                theta.append(np.pi / 2)
            else:
                theta.append(np.arctan(pos_external[i, 1] / pos_external[i, 0]))
        self.angles = theta
        return np.array([theta])

    # Definition of the forward kinematic given joint angles
    def forwardKin(self, angles):

        x = self.robot["links"] * np.cos(angles)
        y = self.robot["links"] * np.sin(angles)
        pos_external = np.array([x, y])
        return pos_external.reshape([2, pos_external.shape[1]])

    # Definition of the inverse dynamics (from kin to torques)
    def inverseDyn(self, pos, vel, acc):
        # positions, velocities and accelerations are expected to be N-by-nV arrays,
        # where N is the number of timesteps and nV is the number of variables
        # if acc.ndim>1:
        #     if acc.shape[1]!=self._angles.shape[0]:
        #         raise Exception("Wrong value format")
        # elif acc.shape!=self._angles.shape:
        #     raise Exception("Wrong value format")
        # torques = acc * self.robot["links"]**2
        torques = self.I * acc + g * self.robot["mass"] * self.robot[
            "links"
        ] / 2 * np.sin(pos)
        return torques

    # Definition of the forward dynamics (from torques to kin)
    def forwardDyn(self, torques):
        # positions, velocities and accelerations are expected to be N-by-nV arrays,
        # where N is the number of timesteps and nV is the number of variables

        return pos, vel, acc

    # Jacobian definition fro specific robot
    def jacobian(self, position):
        return


# TEST
if __name__ == "__main__":

    robot_spec = dict(
        mass=np.array([1.89]), links=np.array([0.42]), I=np.array([0.00189])
    )
    # ICp = np.array([2.0, 2.0, 3.0])
    # ICv = np.array([3.0, 3.0, 4.0])
    ICp = np.array([0.0])
    ICv = np.array([0.0])

    rob = Robot1J(robot=robot_spec, IC_pos=ICp, IC_vel=ICv)

    print("Mass: " + str(rob.mass))
    print("Position: " + str(rob.pos))
    print("Velocity: " + str(rob.vel))

    ext_pos = np.ndarray([1, 2])
    ext_pos[0, :] = [7.0, 10.0]  # Correct
    # ext_pos = np.array([7.0,10.0,3.0])     # Wrong
    # ext_pos = 7.0                          # Wrong
    # ext_pos = np.ones((10,2))              # Correct
    # ext_pos = np.ones((10,3))              # Wrong
    print(rob.inverseKin(ext_pos))

    acc = np.array([3.0, 4.0])  # Correct
    # acc = np.array([3.0,4.0,7.0])           # Wrong
    # acc = 7.0                               # Wrong
    # acc = np.ones((10,2))                   # Correct
    # acc = np.ones((10,3))                   # Wrong
    print(rob.inverseDyn(rob.inverseKin(ext_pos), 0, acc))

    print("Number of variables: " + str(rob.numVariables()))

    # Integration
    dt = 0.01
    # u  = np.array([5.0,3.0])
    u = np.array([0.0, 0.0])
    rob.integrateTimeStep(u, dt)
    print("New position: " + str(rob.pos))
    print("New velocity: " + str(rob.vel))
