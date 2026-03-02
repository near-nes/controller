from enum import Enum
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field

from . import paths as p


class TrajGeneratorType(str, Enum):
    MOCKED = "mocked"
    GLE = "gle"
    # ANN = "ann"


class M1Type(str, Enum):
    MOCKED = "mocked"
    EPROP = "eprop"


class GLETrajGeneratorConfig(BaseModel):
    model_dir: Path = p.ARTIFACTS_PLANNER


class PlannerModuleConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    trajgen_type: TrajGeneratorType = Field(default=TrajGeneratorType.MOCKED)
    gle_config: GLETrajGeneratorConfig = Field(
        default_factory=lambda: GLETrajGeneratorConfig()
    )
    kp: float = 100.0
    kpl: float = 0.32504265346581107
    base_rate: float = 5.0


class M1MockConfig(BaseModel):
    m1_base_rate: float = 0.0
    m1_kp: float = 2000.0296740997816629


class M1EPropConfig(BaseModel):
    config_path: str = p.M1_CONFIG
    weights_path: str = p.M1_WEIGHTS


class MotorCortexModuleConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    m1_type: M1Type = Field(default=M1Type.EPROP)
    m1_mock_config: M1MockConfig = Field(default_factory=lambda: M1MockConfig())
    m1_eprop_config: M1EPropConfig = Field(default_factory=lambda: M1EPropConfig())
    fbk_base_rate: float = 0.0
    fbk_kp: float = 1.0  # 0.20
    out_base_rate: float = 0.0
    out_kp: float = 1.25
    wgt_ffwd_out: float = 1.0
    wgt_fbk_out: float = 0.1  # 2.0 0.25
    buf_sz: float = 50.0


class SpineModuleConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    wgt_motCtx_motNeur: float = 1.0625540740843757
    wgt_sensNeur_spine: float = 1.0  # 1.6427161409427353
    sensNeur_base_rate: float = 0.0
    sensNeur_kp: float = 100.0  # 35.0  # 1200.0
    fbk_delay: float = 1.0  # ms


class StateModuleConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    kp: float = 1.0  # 1.4
    base_rate: float = 0.0
    buffer_size: float = 150.0  # 60.0
    # p: float = 2.0
    # pred_offset: float = -0.0


class StateSEModuleConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    kpred: float = 0.0
    ksens: float = 1.0
    out_base_rate: float = 0.0
    out_kp: float = 1.0
    wgt_scale: float = 1.0
    buf_sz: float = 20.0


class ModuleContainerConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    planner: PlannerModuleConfig = Field(default_factory=lambda: PlannerModuleConfig())
    motor_cortex: MotorCortexModuleConfig = Field(
        default_factory=lambda: MotorCortexModuleConfig()
    )
    spine: SpineModuleConfig = Field(default_factory=lambda: SpineModuleConfig())
    state: StateModuleConfig = Field(default_factory=lambda: StateModuleConfig())
    state_se: StateSEModuleConfig = Field(default_factory=lambda: StateSEModuleConfig())
