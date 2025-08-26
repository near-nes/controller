from typing import ClassVar

from pydantic import BaseModel, Field


class PlannerModuleConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    kp: float = 1255.0503631208485
    kpl: float = 0.32504265346581107
    base_rate: float = 10.0


class MotorCortexModuleConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    ffwd_base_rate: float = 0.0
    ffwd_kp: float = 2000.0296740997816629
    fbk_base_rate: float = 0.0
    fbk_kp: float = 0.20
    out_base_rate: float = 0.0
    out_kp: float = 1.25
    wgt_ffwd_out: float = 0.90
    wgt_fbk_out: float = 0.25
    buf_sz: float = 50.0


class SpineModuleConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    wgt_motCtx_motNeur: float = 1.0625540740843757
    wgt_sensNeur_spine: float = 1.6427161409427353
    sensNeur_base_rate: float = 0.0
    sensNeur_kp: float = 1200.0
    fbk_delay: float = 0.1


class StateModuleConfig(BaseModel):
    model_config: ClassVar = {"frozen": True}
    kp: float = 2.0
    base_rate: float = 0.0
    buffer_size: float = 60.0


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
