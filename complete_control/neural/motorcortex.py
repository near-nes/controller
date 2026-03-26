from typing import Protocol, Tuple

import structlog
from config.core_models import SimulationParams
from config.module_params import (
    M1MockConfig,
    M1Type,
    MotorCortexModuleConfig,
    PlannerModuleConfig,
)
from neural.nest_adapter import nest

from .population_view import PopView


class M1SubModule(Protocol):
    """Structural interface for M1 submodule implementations."""

    def connect(self, source_population): ...
    def get_output_pops(self) -> Tuple: ...


class M1Mock:
    #                motorcommands.txt
    #                        │
    #  ┌─────────┐    ┌──────┼──────────────────────────┐
    #  │         │    │      ▼         Motor Cortex     │
    #  │ Planner │    │  ┌─────────┐       ┌─────────┐  │
    #  │         │----│-▶│  Ffwd   │──────▶│   Out   │  │
    #  │         │    │  │(tracking│       │  (basic │  │
    #  └─────────┘    │  │ neuron) │       │  neuron)│  │
    #       │         │  └─────────┘       └─────────┘  │
    #       │         │                         ▲       │
    #       │  +      │  ┌─────────┐            │       │
    #       └────▶█───┼─▶│   Fbk   │            │       │
    #             ▲   │  │  (diff  │────────────┘       │
    #           - │   │  │  neuron)│                    │
    #             │   │  └─────────┘                    │
    #                 └─────────────────────────────────┘
    def __init__(
        self,
        numNeurons,
        motorCommands,
        params: M1MockConfig,
        sim_steps,
        delay_ms: float,
    ):
        self.N = numNeurons
        self.params = params
        self.motorCommands = motorCommands
        self.delay_ms = delay_ms
        self.sim_steps = sim_steps
        self.create_network()

    def create_network(self):
        par_m1 = {"base_rate": self.params.m1_base_rate, "kp": self.params.m1_kp}
        self.output_p = nest.Create("tracking_neuron_nestml", n=self.N)
        nest.SetStatus(
            self.output_p,
            {
                **par_m1,
                "pos": True,
                "traj": self.motorCommands,
                "simulation_steps": self.sim_steps,
            },
        )

        self.output_n = nest.Create("tracking_neuron_nestml", n=self.N)
        nest.SetStatus(
            self.output_n,
            {
                **par_m1,
                "pos": False,
                "traj": self.motorCommands,
                "simulation_steps": self.sim_steps,
            },
        )
        # self.output_n = PopView(n, to_file=True, label="mc_m1_n")

    def connect(self, source):
        return

    def get_output_pops(self):
        return self.output_p, self.output_n


class MotorCortex:
    #                 ┌─────────────────────────────────┐
    #  ┌─────────┐    │                Motor Cortex     │
    #  │ Planner │    │  ┌─────────┐       ┌─────────┐  │
    #  └─────────┘----│-▶│    M1   │──────▶│   Out   │  │
    #       │         │  └─────────┘       └─────────┘  │
    #       │         │                         ▲       │
    #       │  +      │  ┌─────────┐            │       │
    #       └────▶█───┼─▶│   Fbk   │            │       │
    #             ▲   │  │  (diff  │────────────┘       │
    #           - │   │  │  neuron)│                    │
    #             │   │  └─────────┘                    │
    #                 └─────────────────────────────────┘
    """Module that creates the motor commands

    The MotorCortex has 2 main roles:
    1. translating the Planner's desired trajectory (rate-based) into motor commands
    2. correct motor commands accounting for current state (compared to expected state
        acc to Planner trajectory)

    1 is accomplished by the M1 Submodule. The M1 exists in two versions. A complete one
    based on E-Prop, implemented in https://github.com/shimoura/motor-controller-model;
    and a mock one, implemented above.
    """

    def __init__(
        self,
        numNeurons,
        params: MotorCortexModuleConfig,
        sim: SimulationParams,
        m1_delay: float,
        plan_params: PlannerModuleConfig,
    ):
        self._log = structlog.get_logger("motorcortex")
        self.sim = sim
        self.N = numNeurons
        self.params = params
        self.m1_delay = m1_delay
        self.plan_params = plan_params
        self.create_net(params, numNeurons)

    def create_net(self, params: MotorCortexModuleConfig, numNeurons):
        if params.m1_type == M1Type.EPROP:
            from motor_cortex_eprop.motor_controller_model import m1_factory
            from motor_cortex_eprop.motor_controller_model.config_schema import (
                MotorControllerConfig,
                SimulationConfig,
                TaskConfig,
                TrainingSignalConfig,
            )

            m1_config = MotorControllerConfig(
                simulation=SimulationConfig(step=self.sim.resolution),
                task=TaskConfig(input_shift_ms=self.m1_delay),
                training=TrainingSignalConfig(
                    n_input_neurons=numNeurons,
                    time_move_ms=self.sim.time_move,
                    m1_kp=params.m1_mock_config.m1_kp,
                    m1_base_rate=params.m1_mock_config.m1_base_rate,
                    inertia=self.sim.oracle.robot_spec.I[0],
                    planner_kp=self.plan_params.kp,
                    planner_base_rate=self.plan_params.base_rate,
                ),
            )
            self.m1 = m1_factory.get_m1_or_raise(
                m1_config, params.m1_eprop_config.artifacts_dir
            )
            self.m1.build_network(
                simulation_time_ms=self.sim.duration_ms,
                output_neuron_model="basic_neuron_nestml",
                output_neuron_params={
                    # TODO: this needs to become standard configuration once it stabilizes
                    "simulation_steps": self.sim.sim_steps,
                    "kp": 0.001,
                    "buffer_size": 50,  # 5 for downwards, 50 for upwards
                    # "tau_m": m1_config.neurons.out.tau_m,
                    # "C_m": m1_config.neurons.out.C_m,
                    # "E_L": m1_config.neurons.out.E_L,
                    # "V_th": 70.0,  # tuning knob
                },
                n_out=params.m1_eprop_config.n_out_pop,
            )
            self.conn_type_m1_to_out = "one_to_one"
        else:
            from utils_common.generate_signals_minjerk import (
                generate_motor_commands_minjerk,
            )

            motor_commands = generate_motor_commands_minjerk(self.sim)
            self.m1 = M1Mock(
                numNeurons,
                motor_commands,
                params.m1_mock_config,
                self.sim.sim_steps,
                delay_ms=self.m1_delay,
            )
            self.conn_type_m1_to_out = "one_to_one"

        par_fbk = {"base_rate": params.fbk_base_rate, "kp": params.fbk_kp}
        par_out = {"base_rate": params.out_base_rate, "kp": params.out_kp}
        buf_sz = params.buf_sz

        m1_out_p, m1_out_n = self.m1.get_output_pops()
        self.m1_out_p = PopView(m1_out_p, to_file=True, label="mc_m1_p")
        self.m1_out_n = PopView(m1_out_n, to_file=True, label="mc_m1_n")

        self.fbk_p = None
        self.fbk_n = None
        self.out_p = None
        self.out_n = None

        ############ FEEDBACK ############
        tmp_pop_p = nest.Create("diff_neuron_nestml", n=numNeurons, params=par_fbk)
        nest.SetStatus(
            tmp_pop_p,
            {
                "pos": True,
                "buffer_size": buf_sz,
                "simulation_steps": self.sim.sim_steps,
            },
        )
        self.fbk_p = PopView(tmp_pop_p, to_file=True, label="mc_fbk_p")

        tmp_pop_n = nest.Create("diff_neuron_nestml", n=numNeurons, params=par_fbk)
        nest.SetStatus(
            tmp_pop_n,
            {
                "pos": False,
                "buffer_size": buf_sz,
                "simulation_steps": self.sim.sim_steps,
            },
        )
        self.fbk_n = PopView(tmp_pop_n, to_file=True, label="mc_fbk_n")

        ############ OUTPUT ############
        tmp_pop_p = nest.Create("basic_neuron_nestml", n=numNeurons, params=par_out)
        nest.SetStatus(
            tmp_pop_p,
            {
                "pos": True,
                "buffer_size": buf_sz,
                "simulation_steps": self.sim.sim_steps,
            },
        )
        self.out_p = PopView(tmp_pop_p, to_file=True, label="mc_out_p")

        tmp_pop_n = nest.Create("basic_neuron_nestml", n=numNeurons, params=par_out)
        nest.SetStatus(
            tmp_pop_n,
            {
                "pos": False,
                "buffer_size": buf_sz,
                "simulation_steps": self.sim.sim_steps,
            },
        )
        self.out_n = PopView(tmp_pop_n, to_file=True, label="mc_out_n")
        # self.connect_m1_to_out()

        nest.Connect(
            self.fbk_p.pop,
            self.out_p.pop,
            "one_to_one",
            {"weight": params.wgt_fbk_out},
        )
        nest.Connect(
            self.fbk_p.pop,
            self.out_n.pop,
            "one_to_one",
            {"weight": params.wgt_fbk_out},
        )
        nest.Connect(
            self.fbk_n.pop,
            self.out_p.pop,
            "one_to_one",
            {"weight": -params.wgt_fbk_out},
        )
        nest.Connect(
            self.fbk_n.pop,
            self.out_n.pop,
            "one_to_one",
            {"weight": -params.wgt_fbk_out},
        )
        self.connect_m1_to_out()

    def connect_m1_to_out(self):
        nest.Connect(
            self.m1_out_p.pop,
            self.out_p.pop,
            self.conn_type_m1_to_out,
            {"weight": self.params.wgt_ffwd_out},
        )
        nest.Connect(
            self.m1_out_p.pop,
            self.out_n.pop,
            self.conn_type_m1_to_out,
            {"weight": self.params.wgt_ffwd_out},
        )
        nest.Connect(
            self.m1_out_n.pop,
            self.out_p.pop,
            self.conn_type_m1_to_out,
            {"weight": -self.params.wgt_ffwd_out},
        )
        nest.Connect(
            self.m1_out_n.pop,
            self.out_n.pop,
            self.conn_type_m1_to_out,
            {"weight": -self.params.wgt_ffwd_out},
        )

    def connect_planner_to_m1(self, planner_p: PopView, planner_n: PopView):
        self.m1.connect(planner_p.pop)
