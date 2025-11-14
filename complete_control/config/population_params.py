from typing import ClassVar, Dict

from pydantic import BaseModel, Field


class SinglePopParams(BaseModel):
    model_config: ClassVar = {"frozen": True}
    kp: float
    buffer_size: float
    base_rate: float


class RBFPopParams(SinglePopParams):
    sdev: float
    freq_max: float


class PopulationsParams(BaseModel):
    model_config: ClassVar = {"frozen": True}
    prediction: SinglePopParams = Field(
        default_factory=lambda: SinglePopParams(
            kp=1.0, buffer_size=20.0, base_rate=1.0
        )  # 50
    )
    motor_commands: RBFPopParams = Field(
        default_factory=lambda: RBFPopParams(
            kp=3.0, buffer_size=5.0, base_rate=5.0, sdev=4.0, freq_max=40
        )
    )
    brain_stem: SinglePopParams = Field(
        default_factory=lambda: SinglePopParams(kp=0.2, buffer_size=10.0, base_rate=0.0)
    )
    feedback: SinglePopParams = Field(
        default_factory=lambda: SinglePopParams(kp=1.0, buffer_size=10.0, base_rate=0.0)
    )
    fbk_smoothed: SinglePopParams = Field(
        default_factory=lambda: SinglePopParams(
            kp=1.0, buffer_size=150.0, base_rate=1.0
        )
    )
    error: SinglePopParams = Field(
        default_factory=lambda: SinglePopParams(
            kp=1.0, buffer_size=30.0, base_rate=-1.0  # 20.0
        )
    )
    plan_to_inv: RBFPopParams = Field(
        default_factory=lambda: RBFPopParams(
            kp=3.0, buffer_size=5.0, base_rate=5.0, sdev=4.0, freq_max=40
        )
    )
    state_to_inv: SinglePopParams = Field(
        default_factory=lambda: SinglePopParams(kp=1.0, buffer_size=10.0, base_rate=0.0)
    )
    motor_pred: SinglePopParams = Field(
        default_factory=lambda: SinglePopParams(
            kp=0.05, buffer_size=20.0, base_rate=40.0
        )
    )
    feedback_inv: SinglePopParams = Field(
        default_factory=lambda: SinglePopParams(kp=1.0, buffer_size=10.0, base_rate=0.0)
    )
    error_i: SinglePopParams = Field(
        default_factory=lambda: SinglePopParams(
            kp=1.0, buffer_size=30.0, base_rate=-20.0
        )
    )
