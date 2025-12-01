from dataclasses import astuple, dataclass
from pathlib import Path
from typing import ClassVar, Iterator, List

import numpy as np
import structlog
from pydantic import BaseModel
from utils_common.custom_types import NdArray

_log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@dataclass
class JointState:
    pos: float
    vel: float

    # to be able to do: pos, vel = joint_state
    def __iter__(self) -> Iterator[float]:
        return iter(astuple(self))


@dataclass
class JointStates:
    shoulder: JointState
    elbow: JointState
    hand: JointState

    def __iter__(self) -> Iterator[JointState]:
        yield self.shoulder
        yield self.elbow
        yield self.hand


class EEData(BaseModel):
    """Holds time-series data for end effector"""

    pos_ee: NdArray
    vel_ee: NdArray

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def empty(cls, num_total_steps: int):
        return cls(
            pos_ee=np.zeros([num_total_steps, 3]),
            vel_ee=np.zeros([num_total_steps, 2]),
        )

    def record_step(self, step, pos_ee, vel_ee):
        if step < 0 or step >= self.pos_ee.shape[0]:
            _log.error(
                "Step index out of bounds for data recording",
                step=step,
                max_steps=self.pos_ee.shape[0],
            )
            return
        self.pos_ee[step, :] = pos_ee[0:3]
        self.vel_ee[step, :] = [vel_ee[0], vel_ee[2]]


class JointData(BaseModel):
    """Holds time-series data for a single joint."""

    pos_rad: NdArray
    vel_rad_s: NdArray
    input_cmd_torque: NdArray

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def empty(cls, num_total_steps: int):
        return cls(
            pos_rad=np.zeros(num_total_steps),
            vel_rad_s=np.zeros(num_total_steps),
            input_cmd_torque=np.zeros(num_total_steps),
        )

    def record_step(
        self,
        step: int,
        joint_pos_rad: float,
        joint_vel_rad_s: float,
        input_cmd_torque: float,
    ):
        """Records data for the current simulation step."""
        if step < 0 or step >= self.pos_rad.shape[0]:
            _log.error(
                "Step index out of bounds for data recording",
                step=step,
                max_steps=self.pos_rad.shape[0],
            )
            return

        self.pos_rad[step] = joint_pos_rad
        self.vel_rad_s[step] = joint_vel_rad_s
        self.input_cmd_torque[step] = input_cmd_torque


class PlantPlotData(BaseModel):
    """Holds all data needed for plotting."""

    joint_data: List[JointData]
    ee_data: EEData
    error: List[float]  # elbow error end of trial
    init_hand_pos_ee: List[float]
    trgt_hand_pos_ee: List[float]

    model_config: ClassVar = {
        "arbitrary_types_allowed": True,
    }

    def save(self, params_path: Path):
        """Saves all collected simulation data to a single JSON file."""
        _log.info(f"Saving all simulation data to {params_path}")
        with open(params_path, "w") as f:
            f.write(self.model_dump_json(indent=2))
        _log.info("Finished saving all data.")

    @classmethod
    def load(cls, params_path: Path):
        """Loads the main plant data model from a JSON file."""
        _log.info(f"Loading plant data from {params_path}")
        with open(params_path, "r") as f:
            return cls.model_validate_json(f.read())
