from typing import ClassVar, Optional

from pydantic import BaseModel, Field, computed_field

# set min delay >=resolution
min_delay = 1.0  # ms


class SingleSynapseParams(BaseModel):
    model_config: ClassVar = {"frozen": True}

    synapse_model: str = "static_synapse"
    weight: float
    delay: Optional[float] = None
    receptor_type: Optional[int] = None


class ConnectionsParams(BaseModel):
    model_config: ClassVar = {"frozen": True}

    sensory_delay: float = 150
    m1_delay: float = 100.0  # ms - M1 processing delay (trajectory → motor commands)

    # atm dcn_f->pred : AtoA conn
    dcn_forw_prediction: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.046,  # (1/65)*3
            delay=min_delay,
        )
    )
    pred_state: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.005,
            delay=min_delay,
        )
    )
    sensory_delayed_state: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.005,
            delay=min_delay,
        )
    )
    sn_state: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.6317663917438847,
            receptor_type=2,
        )
    )
    state_mc_fbk: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=-1.0,  # 1.67,  # -2.75,  # 1.875,  #   -1.2,
            delay=min_delay,
        )
    )
    mc_out_motor_commands: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.25,  # 1.0
            delay=min_delay,
        )
    )
    motor_commands_mossy_forw: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=1.0,
            delay=min_delay,
        )
    )
    """
    sn_feedback: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.005,
            delay=min_delay,
        )
    )
    """
    error_io_f: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.7,
            delay=min_delay,
            receptor_type=1,
        )
    )
    state_state_to_inv: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.005,  # 0.020,
            delay=min_delay,
        )
    )
    state_to_inv_error_inv: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=-0.005,
            delay=min_delay,
        )
    )
    plan_to_inv_mossy: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=1.0,
            delay=min_delay,
        )
    )
    dcn_i_motor_pred: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.5,
            delay=min_delay,
        )
    )
    motor_pred_mc_out: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.1,
            delay=min_delay,
        )
    )
    motor_pre_brain_stem: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.005,
            delay=min_delay,
        )
    )
    mc_out_brain_stem: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.005,  # 0.1,
            delay=min_delay,
        )
    )
    state_error_inv: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.5,
            delay=min_delay,
        )
    )
    plan_to_inv_error_inv: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=1.0,
            delay=min_delay,
        )
    )
    error_inv_io_i: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.8,
            delay=min_delay,
            receptor_type=1,
        )
    )

    sensory_delayed_error: SingleSynapseParams = Field(
        default_factory=lambda: SingleSynapseParams(
            weight=0.005,
            delay=min_delay,
        )
    )

    @computed_field
    @property
    def planner_mc_fbk(self) -> SingleSynapseParams:
        return SingleSynapseParams(weight=1.0, delay=self.m1_delay)

    @computed_field
    @property
    def planner_plan_to_inv(self) -> SingleSynapseParams:
        return SingleSynapseParams(weight=0.25, delay=self.m1_delay)

    @computed_field
    @property
    def planner_error_inv(self) -> SingleSynapseParams:
        return SingleSynapseParams(weight=0.005, delay=self.m1_delay)

    @computed_field
    @property
    def sn_fbk_smoothed(self) -> SingleSynapseParams:
        return SingleSynapseParams(weight=0.005, delay=self.sensory_delay)

    @computed_field
    @property
    def state_error_fwd(self) -> SingleSynapseParams:
        return SingleSynapseParams(weight=-0.005, delay=self.sensory_delay)
