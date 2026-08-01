"""Abstract interface for plant simulators.

This module defines the PlantInterface ABC that any physics engine implementation
(PyBullet, MuJoCo, etc.) must satisfy. This allows PlantSimulator to remain
simulator-agnostic.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple


class PlantInterface(ABC):
    """Abstract interface for robotic plant implementations.
    
    Any simulator backend (PyBullet, MuJoCo, etc.) should inherit from this
    and implement all abstract methods to be compatible with PlantSimulator.
    """

    @abstractmethod
    def get_joint_states(self):
        """Return current state of all joints.
        
        Returns:
            JointStates object containing position and velocity for each joint.
        """
        pass

    @abstractmethod
    def get_ee_pose_and_velocity(self) -> Tuple[List[float], List[float]]:
        """Return end-effector position and velocity.
        
        Returns:
            Tuple of (ee_position_m, ee_velocity_m_s)
        """
        pass

    @abstractmethod
    def check_target_proximity(self) -> bool:
        """Check if end-effector is close enough to grasp target.
        
        Returns:
            True if within grasping distance, False otherwise.
        """
        pass

    @abstractmethod
    def grasp(self) -> None:
        """Execute grasping action to attach target object."""
        pass

    @abstractmethod
    def move_shoulder(self, direction: float) -> None:
        """Move shoulder in specified direction.
        
        Args:
            direction: Direction of movement (positive/negative).
        """
        pass

    @abstractmethod
    def update_ball_position(self) -> None:
        """Update position of grasped object relative to hand."""
        pass

    @abstractmethod
    def set_elbow_joint_torque(self, torques: List[float]) -> None:
        """Apply torque to elbow joint.
        
        Args:
            torques: List of torque values in Nm.
        """
        pass

    @abstractmethod
    def lock_elbow_joint(self) -> None:
        """Lock elbow joint (no torque applied)."""
        pass

    @abstractmethod
    def simulate_step(self) -> None:
        """Execute one physics simulation step."""
        pass

    @abstractmethod
    def _capture_state_and_save(self, path, axis=None) -> None:
        """Capture visual state and save to file.
        
        Args:
            path: Path to save image to.
            axis: Camera axis for rendering (optional).
        """
        pass
