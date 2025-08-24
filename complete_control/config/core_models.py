from enum import Enum
from typing import List

import numpy as np
from pydantic import BaseModel, Field, computed_field


class TargetColor(Enum):
    # RGBA
    BLUE_LEFT = [0, 0, 1, 1]
    RED_RIGHT = [1, 0, 0, 1]


from utils_common.git_utils import get_git_commit_hash

from . import paths


class MetaInfo(BaseModel, frozen=True):
    controller_commit_hash: str = Field(
        default_factory=lambda: get_git_commit_hash(paths.ROOT)
    )
    cerebellum_commit_hash: str = Field(
        default_factory=lambda: get_git_commit_hash(paths.CEREBELLUM)
    )
    run_id: str


class RobotSpecParams(BaseModel, frozen=True):
    mass: List[float] = [1.89]
    links: List[float] = [0.31]
    I: List[float] = [0.00189]


class ExperimentParams(BaseModel, frozen=True):
    enable_gravity: bool = False
    z_gravity_magnitude: float = 9.81  # m/s^2
    gravity_trial_start: int = 0  # gravity turns ON at start of this trial
    gravity_trial_end: int = 1  # gravity turns OFF at end of this trial


class OracleData(BaseModel):
    init_joint_angle: float = 90
    tgt_joint_angle: float = 20
    target_visual_offset: float = 4.0
    target_color: TargetColor = Field(default=TargetColor.BLUE_LEFT)
    robot_spec: RobotSpecParams = Field(default_factory=lambda: RobotSpecParams())

    @computed_field
    @property
    def init_pos_angle_rad(self) -> float:
        return np.deg2rad(self.init_joint_angle)

    @computed_field
    @property
    def tgt_pos_angle_rad(self) -> float:
        return np.deg2rad(self.tgt_joint_angle)

    @property
    def tgt_visual_offset_rad(self) -> float:
        return np.deg2rad(self.target_visual_offset)


class SimulationParams(BaseModel, frozen=True):
    resolution: float = 0.1  # ms
    time_prep: float = 150.0  # ms
    time_move: float = 500.0  # ms
    time_post: float = 50.0  # ms
    n_trials: int = 1

    oracle: OracleData = Field(default_factory=lambda: OracleData())

    seed: int = 12345

    @computed_field
    @property
    def duration_single_trial_ms(self) -> float:
        return self.time_prep + self.time_move + self.time_post

    @computed_field
    @property
    def total_duration_all_trials_ms(self) -> float:
        return self.duration_single_trial_ms * self.n_trials

    @classmethod
    def get_default(cls, field_name: str):
        """Get default value for any field"""
        return cls.model_fields[field_name].default

    @classmethod
    def get_default_seed(cls):
        return cls.model_fields["seed"].default

    @property
    def sim_steps(self) -> int:
        return int(self.total_duration_all_trials_ms / self.resolution)

    @property
    def neural_control_steps(self) -> int:
        return int((self.time_prep + self.time_move) / self.resolution)

    @property
    def manual_control_steps(self) -> int:
        return int(self.time_post / self.resolution)


class BrainParams(BaseModel, frozen=True):
    population_size: int = 50
    first_id_sens_neurons: int = 0  # not sure why we need this.


class MusicParams(BaseModel, frozen=True):
    const: float = 1e-6  # Constant to subtract to avoid rounding errors (ms)
    input_latency: float = 0.0001  # seconds
    # neural side ports
    port_motcmd_out: str = "mot_cmd_out"
    port_fbk_in: str = "fbk_in"
    # robotic side ports
    port_motcmd_in: str = "mot_cmd_in"
    port_fbk_out: str = "fbk_out"
