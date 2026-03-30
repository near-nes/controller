"""Generic body class"""

__authors__ = "Cristiano Alessandro"
__copyright__ = "Copyright 2021"
__credits__ = ["Cristiano Alessandro"]
__license__ = "GPL"
__version__ = "1.0.1"


class Body:

    def __init__(self, IC_pos, IC_vel):
        self._pos = IC_pos
        self._vel = IC_vel

    # State variables getters
    @property
    def pos(self):
        return self._pos

    @property
    def vel(self):
        return self._vel

    # State variables setters
    @pos.setter
    def pos(self, value):
        self._pos = value

    @vel.setter
    def vel(self, value):
        self._vel = value

    # Return the number of position variables
    def numVariables(self):
        return len(self._pos)

    # Returns the values of the state variable corresponding to the values of
    # the given external variables
    def inverseKin(self):
        raise Exception("Implement inverse kinematics in derived class")

    # Returns the values of the external variables corresponding to the values of
    # the given state variables
    def forwardKin(self):
        raise Exception("Implement forward kinematics in derived class")

    # Returns the values of the motor commands corresponding to the values of
    # the given state variables
    def inverseDyn(self):
        raise Exception("Implement inverse dynamics in derived class")

    # Returns the value of the Jacobian matrix
    def jacobian(self, position):
        raise Exception("Implement Jacobian in derived class")
