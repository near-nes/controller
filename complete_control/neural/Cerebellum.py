from collections import defaultdict
from pathlib import Path

import numpy as np
import structlog
import tqdm
from bsb import SimulationData, config, from_storage, get_simulation_adapter, options
from bsb_nest.adapter import NestAdapter, NestResult
from config.bsb_models import BSBConfigPaths
from config.connection_params import ConnectionsParams
from mpi4py import MPI
from neural.nest_adapter import nest
from neural.neural_models import SynapseBlock, SynapseRecording
from utils_common.profile import Profile

from .CerebellumPopulations import CerebellumPopulations
from .population_view import PopView

SIMULATION_NAME_IN_YAML = "basal_activity"
DUMMY_MODEL_NAME = "dummy_connection"
PLASTICITY_TYPES = ("stdp_synapse_sinexp", "stdp_synapse_alpha")


def create_key_plastic_connection(s: str, t: str):
    return f"{s}>{t}"


class Cerebellum:
    def __init__(
        self,
        comm: MPI.Comm,
        paths: BSBConfigPaths,
        conn_params: ConnectionsParams,
        total_time_vect: np.ndarray,
        label_prefix: str,
        weights: list[Path] | None,
    ):
        self.log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)
        options.verbosity = (
            0  # TODO how to we handle this verbosity? keep 0 for now but...
        )
        self.total_time_vect = total_time_vect
        self.conn_params = conn_params
        self.label_prefix = label_prefix
        self.populations = CerebellumPopulations()
        self.forward_model = None

        adapter: NestAdapter = get_simulation_adapter("nest", comm)

        conf_forward: config.Configuration = config.parse_configuration_file(
            str(paths.forward_yaml)
        )
        conf_inverse: config.Configuration = config.parse_configuration_file(
            str(paths.inverse_yaml)
        )

        self.forward_model = from_storage(str(paths.cerebellum_hdf5), comm)
        self.forward_model.simulations[SIMULATION_NAME_IN_YAML] = (
            conf_forward.simulations[SIMULATION_NAME_IN_YAML]
        )
        self.log.debug("loaded forward model and its configuration")

        self.inverse_model = from_storage(str(paths.cerebellum_hdf5), comm)
        self.inverse_model.simulations[SIMULATION_NAME_IN_YAML] = (
            conf_inverse.simulations[SIMULATION_NAME_IN_YAML]
        )
        self.log.debug("loaded inverse model and its configuration")

        simulation_forw = self.forward_model.get_simulation(SIMULATION_NAME_IN_YAML)
        simulation_inv = self.inverse_model.get_simulation(SIMULATION_NAME_IN_YAML)

        adapter.simdata[simulation_forw] = SimulationData(
            simulation_forw, result=NestResult(simulation_forw)
        )
        adapter.simdata[simulation_inv] = SimulationData(
            simulation_inv, result=NestResult(simulation_inv)
        )

        adapter.load_modules(simulation_forw)
        adapter.load_modules(simulation_inv)

        # let's just keep the settings we set for the rest of the simulation. specifically, the seed
        # adapter.set_settings(simulation_forw)
        # adapter.set_settings(simulation_inv)

        self.log.debug(
            f"duration: FWD:{simulation_forw.duration}; INV{simulation_inv.duration}"
        )
        self.log.debug(
            f"resolution: FWD:{simulation_forw.resolution}; INV{simulation_inv.resolution}"
        )

        adapter.create_neurons(simulation_forw)
        adapter.create_neurons(simulation_inv)
        self.log.debug("created cerebellum neurons")

        adapter.connect_neurons(simulation_forw)
        adapter.connect_neurons(simulation_inv)
        self.log.debug("connected cerebellum neurons")

        adapter.create_devices(simulation_forw)
        adapter.create_devices(simulation_inv)
        self.log.debug("created cerebellum devices")

        ### FORWARD MODEL
        # Mossy fibers
        self.forw_Nest_Mf = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "mossy_fibers"
        )
        self.N_mossy_forw = len(self.forw_Nest_Mf)

        # Glomerulus
        _forw_N_Glom_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "glomerulus"
        )
        # Granule cells
        _forw_N_GrC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "granule_cell"
        )
        # Golgi cells
        _forw_N_GoC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "golgi_cell"
        )
        # Basket cells
        _forw_N_BC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "basket_cell"
        )
        # Stellate cells
        _forw_N_SC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "stellate_cell"
        )
        # IO
        _forw_N_IO_plus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "io_plus"
        )
        _forw_N_IO_minus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "io_minus"
        )
        # DCN
        _forw_N_DCNp_plus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "dcn_p_plus"
        )
        _forw_N_DCNp_minus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "dcn_p_minus"
        )
        _forw_N_DCNi_plus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "dcn_i_plus"
        )
        _forw_N_DCNi_minus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "dcn_i_minus"
        )
        # PC
        _forw_N_PC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "purkinje_cell_plus"
        )
        _forw_N_PC_minus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_forw
            ].populations.items()
            if neuron_model.name == "purkinje_cell_minus"
        )

        ### INVERSE MODEL
        # Mossy fibers
        self.inv_Nest_Mf = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "mossy_fibers"
        )
        self.N_mossy_inv = len(self.inv_Nest_Mf)

        # Glomerulus
        _inv_N_Glom_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "glomerulus"
        )
        # Granule cells
        _inv_N_GrC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "granule_cell"
        )
        # Golgi cells
        _inv_N_GoC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "golgi_cell"
        )
        # Basket cells
        _inv_N_BC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "basket_cell"
        )
        # Stellate cells
        _inv_N_SC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "stellate_cell"
        )
        # IO
        _inv_N_IO_plus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "io_plus"
        )
        _inv_N_IO_minus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "io_minus"
        )
        # DCN
        _inv_N_DCNp_plus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "dcn_p_plus"
        )
        _inv_N_DCNp_minus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "dcn_p_minus"
        )
        _inv_N_DCNi_plus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "dcn_i_plus"
        )
        _inv_N_DCNi_minus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "dcn_i_minus"
        )
        # PC
        _inv_N_PC_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "purkinje_cell_plus"
        )
        _inv_N_PC_minus_gids = next(
            gids
            for neuron_model, gids in adapter.simdata[
                simulation_inv
            ].populations.items()
            if neuron_model.name == "purkinje_cell_minus"
        )

        self._create_core_pop_views(
            _forw_N_Glom_gids,
            _forw_N_GrC_gids,
            _forw_N_GoC_gids,
            _forw_N_BC_gids,
            _forw_N_SC_gids,
            _forw_N_IO_plus_gids,
            _forw_N_IO_minus_gids,
            _forw_N_DCNp_plus_gids,
            _forw_N_DCNp_minus_gids,
            _forw_N_PC_gids,
            _forw_N_PC_minus_gids,
            _inv_N_Glom_gids,
            _inv_N_GrC_gids,
            _inv_N_GoC_gids,
            _inv_N_BC_gids,
            _inv_N_SC_gids,
            _inv_N_IO_plus_gids,
            _inv_N_IO_minus_gids,
            _inv_N_DCNp_plus_gids,
            _inv_N_DCNp_minus_gids,
            _inv_N_PC_gids,
            _inv_N_PC_minus_gids,
        )

        self.plastic_pairs = [
            (
                self.populations.forw_grc_view,
                self.populations.forw_pc_p_view,
                self._find_receptor_type(
                    conf_forward, "parallel_fiber_to_purkinje_plus"
                ),
            ),
            (
                self.populations.forw_grc_view,
                self.populations.forw_pc_n_view,
                self._find_receptor_type(
                    conf_forward, "parallel_fiber_to_purkinje_minus"
                ),
            ),
            (
                self.populations.inv_grc_view,
                self.populations.inv_pc_p_view,
                self._find_receptor_type(
                    conf_inverse, "parallel_fiber_to_purkinje_plus"
                ),
            ),
            (
                self.populations.inv_grc_view,
                self.populations.inv_pc_n_view,
                self._find_receptor_type(
                    conf_inverse, "parallel_fiber_to_purkinje_minus"
                ),
            ),
        ]
        self._update_weight_plastic_pops(weights)

    def _create_core_pop_views(
        self,
        _forw_N_Glom_gids,
        _forw_N_GrC_gids,
        _forw_N_GoC_gids,
        _forw_N_BC_gids,
        _forw_N_SC_gids,
        _forw_N_IO_plus_gids,
        _forw_N_IO_minus_gids,
        _forw_N_DCNp_plus_gids,
        _forw_N_DCNp_minus_gids,
        _forw_N_PC_gids,
        _forw_N_PC_minus_gids,
        _inv_N_Glom_gids,
        _inv_N_GrC_gids,
        _inv_N_GoC_gids,
        _inv_N_BC_gids,
        _inv_N_SC_gids,
        _inv_N_IO_plus_gids,
        _inv_N_IO_minus_gids,
        _inv_N_DCNp_plus_gids,
        _inv_N_DCNp_minus_gids,
        _inv_N_PC_gids,
        _inv_N_PC_minus_gids,
    ):
        """Creates PopView instances for all core NEST populations."""
        # Forward Model PopViews
        self.populations.forw_mf_view = PopView(
            self.forw_Nest_Mf,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_mf",
        )
        self.populations.forw_glom_view = PopView(
            _forw_N_Glom_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_glom",
        )
        self.populations.forw_grc_view = PopView(
            _forw_N_GrC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_grc",
        )
        self.populations.forw_goc_view = PopView(
            _forw_N_GoC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_goc",
        )
        self.populations.forw_bc_view = PopView(
            _forw_N_BC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_bc",
        )
        self.populations.forw_sc_view = PopView(
            _forw_N_SC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_sc",
        )
        self.populations.forw_io_p_view = PopView(
            _forw_N_IO_plus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_io_p",
        )
        self.populations.forw_io_n_view = PopView(
            _forw_N_IO_minus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_io_n",
        )
        self.populations.forw_dcnp_p_view = PopView(
            _forw_N_DCNp_plus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_dcnp_p",
        )
        self.populations.forw_dcnp_n_view = PopView(
            _forw_N_DCNp_minus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_dcnp_n",
        )
        self.populations.forw_pc_p_view = PopView(
            _forw_N_PC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_pc_p",
        )
        self.populations.forw_pc_n_view = PopView(
            _forw_N_PC_minus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}forw_pc_n",
        )

        # Inverse Model PopViews
        self.populations.inv_mf_view = PopView(
            self.inv_Nest_Mf,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_mf",
        )
        self.populations.inv_glom_view = PopView(
            _inv_N_Glom_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_glom",
        )
        self.populations.inv_grc_view = PopView(
            _inv_N_GrC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_grc",
        )
        self.populations.inv_goc_view = PopView(
            _inv_N_GoC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_goc",
        )
        self.populations.inv_bc_view = PopView(
            _inv_N_BC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_bc",
        )
        self.populations.inv_sc_view = PopView(
            _inv_N_SC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_sc",
        )
        self.populations.inv_io_p_view = PopView(
            _inv_N_IO_plus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_io_p",
        )
        self.populations.inv_io_n_view = PopView(
            _inv_N_IO_minus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_io_n",
        )
        self.populations.inv_dcnp_p_view = PopView(
            _inv_N_DCNp_plus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_dcnp_p",
        )
        self.populations.inv_dcnp_n_view = PopView(
            _inv_N_DCNp_minus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_dcnp_n",
        )
        self.populations.inv_pc_p_view = PopView(
            _inv_N_PC_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_pc_p",
        )
        self.populations.inv_pc_n_view = PopView(
            _inv_N_PC_minus_gids,
            self.total_time_vect,
            to_file=True,
            label=f"{self.label_prefix}inv_pc_n",
        )

    def _find_receptor_type(self, c: config.Configuration, connection_name: str):
        return (
            c.simulations[SIMULATION_NAME_IN_YAML]
            .connection_models[connection_name]
            .synapse.receptor_type
        )

    def get_plastic_connections(self):
        conns = {}
        pairs = self.plastic_pairs
        tot_syn = 0
        for pre_pop, post_pop, receptor_type in pairs:
            c = []
            for p in PLASTICITY_TYPES:
                c.extend(
                    nest.GetConnections(
                        source=pre_pop.pop,
                        target=post_pop.pop,
                        synapse_model=p,
                    )
                    or []
                )
            # receptor_type saved because https://github.com/near-nes/controller/issues/102#issuecomment-3558895210
            conns[(pre_pop.label, post_pop.label)] = (c, receptor_type)
            tot_syn += len(c)

        self.log.debug(
            f"total number of synapses (per process): {tot_syn}", log_all_ranks=True
        )
        return conns

    def _pop_this_id_is_in(self, id):
        return next(i.label for _, i in self.populations if id in i.pop)

    def _update_weight_plastic_pops(self, weights: list[Path]):
        if weights is None:
            return
        create_plastic = Profile()

        num_conns_curr_proc = applied_weights = 0
        with create_plastic.time():
            loc_nodes = set(nest.GetNodes(local_only=True).get("global_id"))
            curr_proc_recordings: defaultdict[str, list[SynapseRecording]] = (
                defaultdict(list)
            )
            self.log.debug(f"loading all connections, split by synapse model...")
            # load all connections, split by synapse model
            for path in weights:
                with open(path, "r") as f:
                    block = SynapseBlock.model_validate_json(f.read())
                for conn in block.synapse_recordings:
                    if conn.syn.target in loc_nodes:
                        curr_proc_recordings[conn.syn.synapse_model].append(conn)
                        num_conns_curr_proc += 1
            self.log.debug(f"{curr_proc_recordings.keys()}")

            # iterate based on synapse model
            for syn_model, connections in curr_proc_recordings.items():
                rec_sources, rec_targets = (set(), set())
                recordings: dict[tuple, SynapseRecording] = {}

                # index connections based on key, save sources/targets
                for conn in connections:
                    rec_sources.add(conn.syn.source)
                    rec_targets.add(conn.syn.target)
                    recordings[
                        (
                            conn.syn.source,
                            conn.syn.target,
                            conn.syn.synapse_model,
                            conn.syn.port,
                        )
                    ] = conn

                # collect nest SynapseCollection of this synapse model
                conn_nest = nest.GetConnections(
                    # nest wants a sorted unique list
                    source=nest.NodeCollection(sorted(rec_sources)),
                    target=nest.NodeCollection(sorted(rec_targets)),
                    synapse_model=syn_model,
                )

                if len(conn_nest) != len(recordings):
                    raise ValueError(
                        f"collected inconsistent connections: {len(conn_nest)} collected vs {len(recordings)} recordings"
                    )

                # sort weights according to collected nest connections
                source = conn_nest.get("source")
                target = conn_nest.get("target")
                synapse_model = conn_nest.get("synapse_model")
                port = conn_nest.get("port")
                weights_sorted = []
                for conn, source, target, model, port in zip(
                    conn_nest,
                    source,
                    target,
                    synapse_model,
                    port,
                ):
                    weights_sorted.append(
                        recordings.pop((source, target, model, port)).weight
                    )

                # apply sorted weights according to the existing SynapseCollection
                nest.SetStatus(conn_nest, [{"weight": w} for w in weights_sorted])
                applied_weights += len(weights_sorted)
        self.log.warning(f"applying all weights took: {create_plastic.total_time}")
        if applied_weights != num_conns_curr_proc:
            raise ValueError(
                f"applied_weights != num_conns_curr_proc ({applied_weights} != {num_conns_curr_proc})"
            )
