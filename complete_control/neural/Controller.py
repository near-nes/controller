from collections import defaultdict
from typing import Optional

import numpy as np
import structlog
from config.bsb_models import BSBConfigPaths
from config.connection_params import ConnectionsParams
from config.core_models import MusicParams, SimulationParams
from config.MasterParams import MasterParams
from config.module_params import (
    MotorCortexModuleConfig,
    PlannerModuleConfig,
    SpineModuleConfig,
    StateModuleConfig,
)
from config.population_params import PopulationsParams
from neural.nest_adapter import nest
from plant.sensoryneuron import SensoryNeuron

from .ControllerPopulations import ControllerPopulations
from .motorcortex import MotorCortex
from .population_view import PopView
from .stateestimator import StateEstimator_mass

#                       motorcommands.txt
#                               │
#         ┌─────────┐    ┌──────┼──────────────────────────┐
#  t      │         │    │      ▼         Motor Cortex     │    ┌────────────┐
#  r ────▶│ Planner │    │  ┌─────────┐       ┌─────────┐  │───▶│ Smoothing  │
#  a      │(tracking│----│-▶│  Ffwd   │──────▶│   Out   │  │    └────────────┘      __
#  j.txt  │ neuron) │    │  │(tracking│       │  (basic │  │          |     _(\    |@@|
#         └─────────┘    │  │ neuron) │       │  neuron)│  │          ▼    (__/\__ \--/ __
#              │         │  └─────────┘       └─────────┘  │       robotic    \___|----|  |   __
#              │         │                         ▲       │        plant         \ }{ /\ )_ / _\
#              │  +      │  ┌─────────┐            │       │          │           /\__/\ \__O (__
#              └────▶█───┼─▶│   Fbk   │            │       │          │          (--/\--)    \__/
#                    ▲   │  │  (diff  │────────────┘       │          │          _)(  )(_
#                  - │   │  │  neuron)│                    │          ▼         `---''---`
#                    │   │  └─────────┘                    │    ┌────────────────┐
#                    │   └─────────────────────────────────┘    │    Sensory     │
#                    │                                          │     system     │
#                    │                                          └────────────────┘
#            ┌──────────────┐   ┌───────────────┐                      │
#            │    State     │   │  Fbk_smoothed │◀─────────────────────┘
#            │  estimator   │◀──│ (basic neuron)│
#            │(state neuron)│   └───────────────┘
#            └──────────────┘

NJT = 1


class Controller:
    """
    Encapsulates the NEST network components and connections for a single DoF,
    using PopView for recording and a dataclass for population management.
    """

    def __init__(
        self,
        dof_id: int,
        N: int,
        total_time_vect: np.ndarray,
        trajectory_slice: np.ndarray,
        motor_cmd_slice: np.ndarray,
        mc_params: MotorCortexModuleConfig,
        plan_params: PlannerModuleConfig,
        spine_params: SpineModuleConfig,
        state_params: StateModuleConfig,
        pops_params: PopulationsParams,
        conn_params: ConnectionsParams,
        sim_params: SimulationParams,
        master_params: MasterParams,
        path_data: str,
        comm,  # MPI.Comm
        music_cfg: MusicParams = None,
        label_prefix: str = "",
        use_cerebellum: bool = False,
        cerebellum_paths: Optional[BSBConfigPaths] = None,
    ):
        """
        Initializes the controller for one Degree of Freedom.

        Args:
            ...
            use_cerebellum (bool): Flag to enable/disable cerebellum integration.
            cerebellum_paths: paths for Cerebellum build, required if use_cerebellum is True.
        """
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger(
            f"controller"
        ).bind(controller_dof=dof_id)
        self.log.info("Initializing Controller")
        self.dof_id = dof_id
        self.N = N
        self.total_time_vect = total_time_vect
        self.trajectory_slice = trajectory_slice
        self.motor_cmd_slice = motor_cmd_slice

        self.weights_history = defaultdict(lambda: defaultdict(list))
        self.mc_params = mc_params
        self.plan_params = plan_params
        self.spine_params = spine_params
        self.state_params = state_params
        self.pops_params = pops_params
        self.conn_params = conn_params
        self.sim_params = sim_params
        self.master_params = master_params
        self.music_cfg = music_cfg
        self.path_data = path_data
        self.use_cerebellum = use_cerebellum
        self.cerebellum_paths = cerebellum_paths
        self.comm = comm
        self.label = f"{label_prefix}"

        self.log.debug(
            "Controller Parameters",
            dof_id=dof_id,
            N=N,
            mc_params=mc_params,
            plan_params=plan_params,
            spine_params=spine_params,
            state_params=state_params,
            pops_params=pops_params,
            conn_params=conn_params,
            sim_params=sim_params,
            music_cfg=music_cfg,
            use_cerebellum=self.use_cerebellum,
            cerebellum_config=self.cerebellum_paths,
            comm=self.comm,
        )

        self.pops = ControllerPopulations()
        self.cerebellum_handler = None

        if use_cerebellum:
            self.cerebellum_handler = self._instantiate_cerebellum_handler(self.pops)
        # this order has a reason to it: beside the obvious dependency connect -> create, there is a more insidious one:
        # Cerebellum ALWAYS tries to import custom_stdp, but if it had been imported already NEST will error out
        # (tracking_neuron_nestml already exists, choose a different model name); this means that Cerebellum must be
        # created first, so that its modules are imported -> custom_stdp exists already and does not need to be loaded again

        # --- Build and Connect ---
        self.log.info("Creating controller blocks...")
        self._create_blocks()
        self.log.info("Connecting internal controller blocks...")
        self._connect_blocks_controller()

        # --- Connect Cerebellum and Controller (needs to be here... >:( )
        if use_cerebellum:
            self.cerebellum_handler.connect_to_main_controller_populations()

        self.log.info("Creating coordinator interface...")
        self.enable_music = music_cfg is not None
        if self.enable_music:
            self.create_and_setup_music_interface()
            self.log.info(f"Connecting controller to MUSIC")
            self.connect_controller_to_music()
        else:
            self.create_and_connect_NRP_interface()
            self.log.info(f"Connected controller to NRP proxies")

        self.log.info("Controller initialization complete.")

    def record_synaptic_weights(self, trial: int):
        PF_to_purkinje_conns = (
            self.cerebellum_handler.get_synapse_connections_PF_to_PC()
        )
        for (pre_pop, post_pop), conns in PF_to_purkinje_conns.items():
            for conn in conns:
                source_neur, target_neur, synapse_id, delay, synapse_model, weight = (
                    nest.GetStatus(
                        conn,
                        [
                            "source",
                            "target",
                            "synapse_id",
                            "delay",
                            "synapse_model",
                            "weight",
                        ],
                    )[0]
                )
                self.weights_history[(pre_pop, post_pop)][
                    (source_neur, target_neur, synapse_id, synapse_model)
                ].append(weight)

    def _instantiate_cerebellum_handler(self, controller_pops: ControllerPopulations):
        from .CerebellumHandler import CerebellumHandler

        """Instantiates the internal CerebellumHandler."""
        self.log.info("Instantiating internal CerebellumHandler")
        if self.cerebellum_paths is None:
            raise ValueError(
                "Cerebellum config must be provided when use_cerebellum is True"
            )

        cereb_pop_keys = [
            "prediction",
            "feedback",
            "motor_commands",
            "error",
            "plan_to_inv",
            "state_to_inv",
            "error_i",
            "motor_pred",
            "feedback_inv",
        ]
        cereb_conn_keys = [
            "dcn_forw_prediction",
            "error_io_f",
            "dcn_f_error",  # Fwd connections
            "feedback_error",  # Used by CerebellumHandler for fwd error calculation
            "plan_to_inv_error_inv",
            "state_error_inv",  # Inv error connections (state_error_inv might not exist, handled below)
            "error_inv_io_i",
            "dcn_i_motor_pred",  # Inv connections
            # "sn_feedback_inv" is used by controller.py to connect TO cerebellum_controller, not internally by it.
            # Connections *from* SDC *to* CerebController interfaces are handled in SDC._connect_blocks
            # Connections *from* CerebController *to* SDC interfaces are handled in SDC._connect_blocks
        ]

        # cereb_pops_params = {k: self.pops_params[k] for k in cereb_pop_keys}
        # cereb_conn_params = {k: self.conn_params[k] for k in cereb_conn_keys}
        # TODO different parameter sets could be nice :)
        cereb_pops_params = self.pops_params
        cereb_conn_params = self.conn_params

        try:
            cerebellum_controller = CerebellumHandler(
                N=self.N,
                total_time_vect=self.total_time_vect,
                sim_params=self.sim_params,
                pops_params=cereb_pops_params,
                conn_params=cereb_conn_params,
                cerebellum_paths=self.cerebellum_paths,
                path_data=self.path_data,
                label_prefix=f"{self.label}cereb_",
                dof_id=self.dof_id,
                comm=self.comm,
                controller_pops=controller_pops,
            )
            self.log.info("Internal CerebellumHandler instantiated successfully.")
            return cerebellum_controller
        except Exception as e:
            self.log.error(
                "Failed to instantiate internal CerebellumHandler",
                error=str(e),
                exc_info=True,
            )
            raise

    # --- 1. Block Creation ---
    def _create_blocks(self):
        """Creates all neuron populations using PopView for this DoF."""
        self.log.debug("Building planner block")
        self._build_planner(to_file=True)
        self.log.debug("Building motor cortex block")
        self._build_motor_cortex(to_file=True)
        self.log.debug("Building state estimator block")
        self._build_state_estimator(to_file=True)
        self.log.debug("Building sensory neurons block")
        self._build_sensory_neurons(to_file=True)
        self.log.debug(
            "Building prediction neurons block"
        )  # These are the scaling neurons for cerebellar fwd output or other prediction source
        self._build_prediction_neurons(to_file=True)
        self.log.debug("Building feedback smoothed neurons block")
        self._build_fbk_smoothed_neurons(to_file=True)
        self.log.debug("Building brainstem block")
        self._build_brainstem(to_file=True)

    # --- Helper for PopView Creation ---
    def _create_pop_view(self, nest_pop, base_label: str, to_file: bool) -> PopView:
        """Creates a PopView instance with appropriate label."""
        full_label = f"{self.label}{base_label}" if to_file else ""
        return PopView(
            nest_pop, self.total_time_vect, to_file=to_file, label=full_label
        )

    # --- Build Methods (Example: Planner) ---
    def _build_planner(self, to_file=False):
        p_params = self.plan_params
        N = self.N
        self.log.debug(
            "Initializing Planner sub-module",
            N=N,
            njt=NJT,
            kpl=p_params.kpl,
            base_rate=p_params.base_rate,
            kp=p_params.kp,
        )
        tmp_pop_p = nest.Create(
            "tracking_neuron_nestml",
            n=N,
            params={
                "kp": p_params.kp,
                "base_rate": p_params.base_rate,
                "pos": True,
                "traj": self.trajectory_slice.tolist(),
                "simulation_steps": self.sim_params.sim_steps,
            },
        )
        tmp_pop_n = nest.Create(
            "tracking_neuron_nestml",
            n=N,
            params={
                "kp": p_params.kp,
                "base_rate": p_params.base_rate,
                "pos": False,
                "traj": self.trajectory_slice.tolist(),
                "simulation_steps": self.sim_params.sim_steps,
            },
        )
        self.pops.planner_p = self._create_pop_view(tmp_pop_p, "planner_p", to_file)
        self.pops.planner_n = self._create_pop_view(tmp_pop_n, "planner_n", to_file)

    def _build_motor_cortex(self, to_file=False):
        self.log.debug(
            "Initializing MotorCortex sub-module",
            N=self.N,
            njt=1,
            mc_params=self.mc_params,
        )
        self.mc = MotorCortex(self.N, self.motor_cmd_slice, self.mc_params)
        self.pops.mc_M1_p = self.mc.m1_out_p
        self.pops.mc_M1_n = self.mc.m1_out_n
        self.pops.mc_fbk_p = self.mc.fbk_p
        self.pops.mc_fbk_n = self.mc.fbk_n
        self.pops.mc_out_p = self.mc.out_p
        self.pops.mc_out_n = self.mc.out_n

    def _build_state_estimator(self, to_file=False):
        buf_sz = self.state_params.buffer_size
        N = self.N

        # Parameters for StateEstimator_mass constructor
        # It expects a dictionary, so we convert the Pydantic model
        state_estimator_constructor_params = self.state_params.model_dump()
        state_estimator_constructor_params.update(
            {
                "N_fbk": N,
                "N_pred": N,
                "fbk_bf_size": N * int(buf_sz / self.sim_params.resolution),
                "pred_bf_size": N * int(buf_sz / self.sim_params.resolution),
                # the nestml model has a hardcoded solution to stop any spikes in time_wait
                "time_wait": 0,
            }
        )

        self.log.debug(
            "Initializing StateEstimator_mass",
            N=N,
            njt=NJT,
            state_params=state_estimator_constructor_params,
        )
        self.stEst = StateEstimator_mass(
            N, NJT, self.total_time_vect, **state_estimator_constructor_params
        )
        self.pops.state_p = self.stEst.pops_p[0]
        self.pops.state_n = self.stEst.pops_n[0]

    def _build_sensory_neurons(self, to_file=False):
        """Parrot neurons for sensory feedback input"""
        pop_p = nest.Create("parrot_neuron", self.N)
        self.pops.sn_p = self._create_pop_view(pop_p, "sensoryneur_p", to_file)
        pop_n = nest.Create("parrot_neuron", self.N)
        self.pops.sn_n = self._create_pop_view(pop_n, "sensoryneur_n", to_file)

    def _build_prediction_neurons(self, to_file=False):
        """
        Builds internal prediction neurons (diff_neuron_nestml).
        These neurons always exist to 'scale' the prediction signal before it goes to the State Estimator.
        If cerebellum is used, the prediction signal comes from cerebellum_controller.forw_DCNp_plus/minus,
        which then connects to these pred_p/n neurons.
        """
        self.log.debug("Building prediction scaling neurons (pred_p, pred_n)")
        params = self.pops_params.prediction
        pop_params = {
            "kp": params.kp,
            "buffer_size": params.buffer_size,
            "base_rate": params.base_rate,
            "simulation_steps": self.sim_params.sim_steps,
        }

        pop_p = nest.Create("diff_neuron_nestml", self.N)
        nest.SetStatus(pop_p, {**pop_params, "pos": True})
        self.pops.pred_p = self._create_pop_view(pop_p, "pred_p", to_file)

        pop_n = nest.Create("diff_neuron_nestml", self.N)
        nest.SetStatus(pop_n, {**pop_params, "pos": False})
        self.pops.pred_n = self._create_pop_view(pop_n, "pred_n", to_file)

    def _build_fbk_smoothed_neurons(self, to_file=False):
        """Neurons for smoothing feedback"""
        params = self.pops_params.fbk_smoothed
        pop_params = {
            "kp": params.kp,
            "buffer_size": params.buffer_size,
            "base_rate": params.base_rate,
            "simulation_steps": self.sim_params.sim_steps,
        }
        self.log.debug("Creating feedback neurons", **pop_params)

        pop_p = nest.Create("basic_neuron_nestml", self.N)
        nest.SetStatus(pop_p, {**pop_params, "pos": True})
        self.pops.fbk_smooth_p = self._create_pop_view(pop_p, "fbk_smooth_p", to_file)

        pop_n = nest.Create("basic_neuron_nestml", self.N)
        nest.SetStatus(pop_n, {**pop_params, "pos": False})
        self.pops.fbk_smooth_n = self._create_pop_view(pop_n, "fbk_smooth_n", to_file)

    def _build_brainstem(self, to_file=False):
        """Basic neurons for output stage"""
        params = self.pops_params.brain_stem
        pop_params = {
            "kp": params.kp,
            "buffer_size": params.buffer_size,
            "base_rate": params.base_rate,
            "simulation_steps": self.sim_params.sim_steps,
        }
        self.log.debug("Creating output neurons (brainstem)", **pop_params)

        pop_p = nest.Create("basic_neuron_nestml", self.N)
        nest.SetStatus(pop_p, {**pop_params, "pos": True})
        self.pops.brainstem_p = self._create_pop_view(pop_p, "brainstem_p", to_file)

        pop_n = nest.Create("basic_neuron_nestml", self.N)
        nest.SetStatus(pop_n, {**pop_params, "pos": False})
        self.pops.brainstem_n = self._create_pop_view(pop_n, "brainstem_n", to_file)

    # --- 2. Block Connection ---
    def _connect_blocks_controller(self):
        """Connects the created populations using PopView attributes."""
        self.log.debug("Connecting internal controller blocks")

        # Planner -> M1
        self.mc.connect(self.pops.planner_p, self.pops.planner_n)

        # Planner -> Motor Cortex Feedback Input
        conn_spec = self.conn_params.planner_mc_fbk
        syn_spec_p = conn_spec.model_dump(exclude_none=True)
        syn_spec_n = conn_spec.model_copy(
            update={"weight": -conn_spec.weight}
        ).model_dump(exclude_none=True)
        self.log.debug(
            "Connecting Planner to MC Fbk",
            syn_spec_p=syn_spec_p,
            syn_spec_n=syn_spec_n,
        )
        nest.Connect(
            self.pops.planner_p.pop,
            self.pops.mc_fbk_p.pop,
            "one_to_one",
            syn_spec=syn_spec_p,
        )
        nest.Connect(
            self.pops.planner_p.pop,
            self.pops.mc_fbk_n.pop,
            "one_to_one",
            syn_spec=syn_spec_p,
        )
        nest.Connect(
            self.pops.planner_n.pop,
            self.pops.mc_fbk_p.pop,
            "one_to_one",
            syn_spec=syn_spec_n,
        )
        nest.Connect(
            self.pops.planner_n.pop,
            self.pops.mc_fbk_n.pop,
            "one_to_one",
            syn_spec=syn_spec_n,
        )

        # State Estimator -> Motor Cortex Feedback Input (Inhibitory)
        conn_spec_state_mc_fbk = self.conn_params.state_mc_fbk
        self.log.debug(
            "Connecting StateEst to MC Fbk (Inhibitory)",
            conn_spec=conn_spec_state_mc_fbk,
        )
        nest.Connect(
            self.pops.state_p.pop,
            self.pops.mc_fbk_p.pop,
            "one_to_one",
            syn_spec=conn_spec_state_mc_fbk.model_dump(exclude_none=True),
        )
        nest.Connect(
            self.pops.state_p.pop,
            self.pops.mc_fbk_n.pop,
            "one_to_one",
            syn_spec=conn_spec_state_mc_fbk.model_dump(exclude_none=True),
        )
        # Create a new spec for the negative weight connection
        conn_spec_state_mc_fbk_neg = conn_spec_state_mc_fbk.model_copy(
            update={"weight": -conn_spec_state_mc_fbk.weight}
        )
        nest.Connect(
            self.pops.state_n.pop,
            self.pops.mc_fbk_p.pop,
            "one_to_one",
            syn_spec=conn_spec_state_mc_fbk_neg.model_dump(exclude_none=True),
        )
        nest.Connect(
            self.pops.state_n.pop,
            self.pops.mc_fbk_n.pop,
            "one_to_one",
            syn_spec=conn_spec_state_mc_fbk_neg.model_dump(exclude_none=True),
        )

        # Motor Cortex Output -> Brainstem
        conn_spec_mc_out_bs = self.conn_params.mc_out_brain_stem
        self.log.debug("Connecting MC out to brainstem", conn_spec=conn_spec_mc_out_bs)
        nest.Connect(
            self.pops.mc_out_p.pop,
            self.pops.brainstem_p.pop,
            "all_to_all",
            syn_spec=conn_spec_mc_out_bs.model_dump(exclude_none=True),
        )
        conn_spec_mc_out_bs_neg = conn_spec_mc_out_bs.model_copy(
            update={"weight": -conn_spec_mc_out_bs.weight}
        )
        nest.Connect(
            self.pops.mc_out_n.pop,
            self.pops.brainstem_n.pop,
            "all_to_all",
            syn_spec=conn_spec_mc_out_bs_neg.model_dump(exclude_none=True),
        )

        # Sensory Input -> Feedback Smoothed Neurons
        sn_fbk_sm_spec = self.conn_params.sn_fbk_smoothed
        syn_spec_p = sn_fbk_sm_spec.model_dump(exclude_none=True)
        syn_spec_n = sn_fbk_sm_spec.model_copy(
            update={"weight": -sn_fbk_sm_spec.weight}
        ).model_dump(exclude_none=True)
        self.log.debug(
            "Connecting sensory to smoothing",
            syn_spec_p=syn_spec_p,
            syn_spec_n=syn_spec_n,
        )
        nest.Connect(
            self.pops.sn_p.pop,
            self.pops.fbk_smooth_p.pop,
            "all_to_all",
            syn_spec=syn_spec_p,
        )
        nest.Connect(
            self.pops.sn_n.pop,
            self.pops.fbk_smooth_n.pop,
            "all_to_all",
            syn_spec=syn_spec_n,
        )

        # Connections INTO State Estimator (Using receptor types)
        st_p = self.pops.state_p.pop
        st_n = self.pops.state_n.pop

        fbk_sm_state_spec = self.conn_params.fbk_smoothed_state.model_dump(
            exclude_none=True
        )
        self.log.debug("Connecting smoothed sensory to state", spec=fbk_sm_state_spec)
        for i, pre in enumerate(self.pops.fbk_smooth_p.pop):
            nest.Connect(
                pre,
                st_p,
                "all_to_all",
                syn_spec={**fbk_sm_state_spec, "receptor_type": i + 1},
            )
        for i, pre in enumerate(self.pops.fbk_smooth_n.pop):
            nest.Connect(
                pre,
                st_n,
                "all_to_all",
                syn_spec={**fbk_sm_state_spec, "receptor_type": i + 1},
            )
        # Prediction (self.pops.pred_p/n) -> State Estimator (Receptors N+1 to 2N)
        # These connections are always made, as pred_p/n always exist.
        offset = self.N + 1  # Start receptor types after the first N for sensory
        pred_state_spec = self.conn_params.pred_state.model_dump(exclude_none=True)
        self.log.debug(
            "Connecting self.pops.pred_p/n to state estimator", spec=pred_state_spec
        )
        for i, pre in enumerate(self.pops.pred_p.pop):
            nest.Connect(
                pre,
                st_p,
                "all_to_all",
                syn_spec={**pred_state_spec, "receptor_type": i + offset},
            )
        for i, pre in enumerate(self.pops.pred_n.pop):
            nest.Connect(
                pre,
                st_n,
                "all_to_all",
                syn_spec={**pred_state_spec, "receptor_type": i + offset},
            )
        # Note: The MC Output -> Brainstem connection happens in both cases and is handled above

    # --- MUSIC Setup ---
    def create_and_setup_music_interface(self):
        """Creates MUSIC proxies for input and output."""
        msc_params = self.music_cfg
        spine_params_dict = self.spine_params.model_dump()
        n_total_neurons = 2 * self.N

        out_port_name = msc_params.port_motcmd_out
        in_port_name = msc_params.port_fbk_in
        latency_const = msc_params.const

        # Output proxy
        self.log.info("Creating MUSIC out proxy", port=out_port_name)
        self.proxy_out = nest.Create(
            "music_event_out_proxy", 1, params={"port_name": out_port_name}
        )
        self.log.info(
            "Created MUSIC out proxy", port=out_port_name, gids=self.proxy_out.tolist()
        )

        # Input proxy
        self.proxy_in = nest.Create(
            "music_event_in_proxy", n_total_neurons, params={"port_name": in_port_name}
        )
        self.log.info(
            "Creating MUSIC in proxy", port=in_port_name, channels=n_total_neurons
        )
        for i, n in enumerate(self.proxy_in):
            nest.SetStatus(n, {"music_channel": i})
        self.log.info(
            f"Created MUSIC in proxy: port '{in_port_name}' with {n_total_neurons} channels"
        )

        # We need to tell MUSIC, through NEST, that it's OK (due to the delay)
        # to deliver spikes a bit late. This is what makes the loop possible.
        # Set acceptable latency for the input port
        # Use feedback delay from spine parameters
        fbk_delay = spine_params_dict["fbk_delay"]
        latency = fbk_delay - latency_const
        # if latency < nest.GetKernelStatus("min_delay"):
        #     print(
        #         f"Warning: Calculated MUSIC latency ({latency}) is less than min_delay ({nest.GetKernelStatus('min_delay')}). Clamping to min_delay."
        #     )
        #     latency = nest.GetKernelStatus("min_delay")

        nest.SetAcceptableLatency(in_port_name, latency)
        self.log.info(
            "Set MUSIC acceptable latency", port=in_port_name, latency=latency
        )
        return

    def connect_controller_to_music(self):
        """Connects a single controller's inputs/outputs to MUSIC proxies."""
        self.log.debug("Connecting MUSIC interfaces", N=self.N)
        bs_p, bs_n = self.pops.brainstem_p, self.pops.brainstem_n
        sn_p, sn_n = self.pops.sn_p, self.pops.sn_n

        # Connect Brainstem outputs
        start_channel_out = 0
        # note: previously, there were multiple DoFs, and start_channel_out was 0*N*dof_id
        self.log.debug(
            "Connecting brainstem outputs to MUSIC out proxy",
            start_channel=start_channel_out,
            num_neurons=self.N,
        )
        for i, neuron in enumerate(bs_p.pop):
            nest.Connect(
                neuron,
                self.proxy_out,
                "one_to_one",
                {"music_channel": start_channel_out + i},
            )
        for i, neuron in enumerate(bs_n.pop):
            nest.Connect(
                neuron,
                self.proxy_out,
                "one_to_one",
                {"music_channel": start_channel_out + self.N + i},
            )

        # Connect MUSIC In Proxy to Sensory Neuron inputs
        start_channel_in = 2 * self.N * self.dof_id
        idx_start_p = start_channel_in
        idx_end_p = idx_start_p + self.N
        idx_start_n = idx_end_p
        idx_end_n = idx_start_n + self.N
        delay = self.spine_params.fbk_delay
        wgt = self.spine_params.wgt_sensNeur_spine
        self.log.debug(
            "Connecting MUSIC in proxy to sensory inputs",
            start_channel=start_channel_in,
            num_neurons=self.N,
            delay=delay,
            weight=wgt,
        )
        nest.Connect(
            self.proxy_in[idx_start_p:idx_end_p],
            sn_p.pop,
            "one_to_one",
            {"weight": wgt, "delay": delay},
        )
        nest.Connect(
            self.proxy_in[idx_start_n:idx_end_n],
            sn_n.pop,
            "one_to_one",
            {"weight": wgt, "delay": delay},
        )

    def create_and_connect_NRP_interface(self):
        buffer_len = 10  # ms, right now, only in plant config
        conn_spec = {
            "delay": self.spine_params.fbk_delay,
            "weight": 1,
        }
        self.proxy_out = nest.Create("basic_neuron_nestml", 2)
        nest.SetStatus(
            self.proxy_out,
            {
                "kp": 0,
                "buffer_size": buffer_len,
                "base_rate": 0,
                "simulation_steps": self.sim_params.sim_steps,
                "pos": True,
            },
        )

        nest.Connect(
            self.pops.brainstem_p.pop, self.proxy_out[0], "all_to_all", conn_spec
        )
        nest.Connect(
            self.pops.brainstem_n.pop, self.proxy_out[1], "all_to_all", conn_spec
        )

        # positive
        self.proxy_in_p = SensoryNeuron(
            self.N,
            pos=True,
            idStart=0,
            bas_rate=self.master_params.modules.spine.sensNeur_base_rate,
            kp=self.master_params.modules.spine.sensNeur_kp,
            res=self.sim_params.resolution,
        )
        # negative
        id_start_n = self.N
        self.proxy_in_n = SensoryNeuron(
            self.N,
            pos=False,
            idStart=id_start_n,
            bas_rate=self.master_params.modules.spine.sensNeur_base_rate,
            kp=self.master_params.modules.spine.sensNeur_kp,
            res=self.sim_params.resolution,
        )
        self.proxy_in_gen = nest.Create("inhomogeneous_poisson_generator", 2)
        self.proxy_in_gen_view = self._create_pop_view(
            self.proxy_in_gen, "proxy_in_NRP", True
        )

        self.log.info(
            "Sensory neurons created and connected",
            neurons_per_pop=self.N,
        )
        conn_spec = {
            "weight": self.spine_params.wgt_sensNeur_spine,
            "delay": self.spine_params.fbk_delay,
        }
        nest.Connect(self.proxy_in_gen[0], self.pops.sn_p.pop, "all_to_all", conn_spec)
        nest.Connect(self.proxy_in_gen[1], self.pops.sn_n.pop, "all_to_all", conn_spec)

    def update_sensory_info_from_NRP(self, angle: float, sim_time: float):
        pos = self.proxy_in_p.lam(angle)
        neg = self.proxy_in_n.lam(angle)
        nest.SetStatus(
            self.proxy_in_gen,
            [
                {"rate_times": [sim_time], "rate_values": [pos]},
                {"rate_times": [sim_time], "rate_values": [neg]},
            ],
        )

    def extract_motor_command_NRP(self):
        rate_pos, rate_neg = [
            i / self.N for i in nest.GetStatus(self.proxy_out, "in_rate")[0:2]
        ]

        return rate_pos, rate_neg

    def get_all_recorded_views(self) -> list[PopView]:
        """
        Collects all PopView instances that are configured for recording from
        the main controller populations and, if enabled, from the cerebellum populations.
        """
        all_views = []
        self.log.debug("Collecting views from ControllerPopulations")
        all_views.extend(self.pops.get_all_views())

        if self.use_cerebellum:
            self.log.debug("Collecting views from CerebellumHandler.interface_pops")
            all_views.extend(self.cerebellum_handler.interface_pops.get_all_views())
            all_views.extend(
                self.cerebellum_handler.cerebellum.populations.get_all_views()
            )
        else:
            self.log.debug("Cerebellum not in use, skipping cerebellum views.")

        recorded_views = [view for view in all_views if view and view.label]
        self.log.info(
            f"Collected {len(recorded_views)} views with labels for recording."
        )
        return recorded_views
