import structlog
from config.core_models import SimulationParams
from config.module_params import M1MockConfig, M1Type, MotorCortexModuleConfig
from interfaces.m1_base import M1SubModule
from neural.nest_adapter import nest

from .population_view import PopView


class M1Mock(M1SubModule):
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
        self.output_p = nest.Create("tracking_neuron_nestml", n=self.N, params=par_m1)
        nest.SetStatus(
            self.output_p,
            {
                "pos": True,
                "traj": self.motorCommands,
                "simulation_steps": self.sim_steps,
            },
        )

        self.output_n = nest.Create("tracking_neuron_nestml", n=self.N, params=par_m1)
        nest.SetStatus(
            self.output_n,
            {
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
    ):
        self._log = structlog.get_logger("motorcortex")
        self.sim = sim
        self.N = numNeurons
        self.params = params
        self.m1_delay = m1_delay
        self.create_net(params, numNeurons)

    def create_net(self, params: MotorCortexModuleConfig, numNeurons):
        if params.m1_type == M1Type.EPROP:
            from motor_cortex_eprop.motor_controller_model.M1MotorCortexEprop import (
                M1MotorCortexEprop,
            )

            self.m1 = M1MotorCortexEprop(
                params.m1_eprop_config.config_path,
                params.m1_eprop_config.weights_path,
                self.sim.sim_steps,
                nest,
                expected_delay=self.m1_delay,
                resolution=self.sim.resolution,
            )
            m1_to_out = "all_to_all"
        else:
            from utils_common.generate_signals_minjerk import (
                generate_motor_commands_minjerk,
            )

            motor_commands = generate_motor_commands_minjerk(self.sim, self.m1_delay)
            self.m1 = M1Mock(
                numNeurons,
                motor_commands,
                params.m1_mock_config,
                self.sim.sim_steps,
                delay_ms=self.m1_delay,
            )
            m1_to_out = "one_to_one"

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

        nest.Connect(
            m1_out_p,
            self.out_p.pop,
            m1_to_out,
            {"weight": params.wgt_ffwd_out},
        )
        nest.Connect(
            m1_out_p,
            self.out_n.pop,
            m1_to_out,
            {"weight": params.wgt_ffwd_out},
        )
        nest.Connect(
            m1_out_n,
            self.out_p.pop,
            m1_to_out,
            {"weight": -params.wgt_ffwd_out},
        )
        nest.Connect(
            m1_out_n,
            self.out_n.pop,
            m1_to_out,
            {"weight": -params.wgt_ffwd_out},
        )

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

    def connect(self, planner_p: PopView, planner_n: PopView):
        self.m1.connect(planner_p.pop)
