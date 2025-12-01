from neural.CerebellumHandlerPopulations import CerebellumHandlerPopulationsGeneric
from neural.CerebellumPopulations import CerebellumPopulationsGeneric
from neural.ControllerPopulations import ControllerPopulationsGeneric
from pydantic import BaseModel


class FlatPopulations(
    ControllerPopulationsGeneric[str],
    CerebellumPopulationsGeneric[str],
    CerebellumHandlerPopulationsGeneric[str],
):
    pass


class HierarchicalPopulations(BaseModel):
    controller: ControllerPopulationsGeneric[str]
    cerebellum: CerebellumPopulationsGeneric[str]
    handler: CerebellumHandlerPopulationsGeneric[str]


def create_pop_constants():
    ctrl_data = {k: k for k in ControllerPopulationsGeneric.model_fields}
    cb_data = {k: k for k in CerebellumPopulationsGeneric.model_fields}
    hdl_data = {k: k for k in CerebellumHandlerPopulationsGeneric.model_fields}

    seen = set()
    for population_name in [*ctrl_data.keys(), *cb_data.keys(), *hdl_data.keys()]:
        if population_name in seen:
            raise ValueError(
                f"Naming Collision Detected! \n"
                f"The population '{population_name}' is already defined \n"
                f"Please rename these fields for clarity."
            )
        seen.add(population_name)

    tree = HierarchicalPopulations(
        controller=ControllerPopulationsGeneric[str].model_construct(**ctrl_data),
        cerebellum=CerebellumPopulationsGeneric[str].model_construct(**cb_data),
        handler=CerebellumHandlerPopulationsGeneric[str].model_construct(**hdl_data),
    )

    all_data = {}
    all_data.update(ctrl_data)
    all_data.update(cb_data)
    all_data.update(hdl_data)

    flat = FlatPopulations.model_construct(**all_data)

    return flat, tree


POPS, POPS_TREE = create_pop_constants()
POPS_PAIRED = [
    (POPS.planner_p, POPS.planner_n),
    (POPS.brainstem_p, POPS.brainstem_n),
    (POPS.mc_out_p, POPS.mc_out_n),
    (POPS.mc_M1_p, POPS.mc_M1_n),
    (POPS.mc_fbk_p, POPS.mc_fbk_n),
    (POPS.state_p, POPS.state_n),
    (POPS.sn_p, POPS.sn_n),
    (POPS.forw_dcnp_p, POPS.forw_dcnp_n),
    (POPS.forw_io_p, POPS.forw_io_n),
    (POPS.forw_pc_p, POPS.forw_pc_n),
    (POPS.inv_dcnp_p, POPS.inv_dcnp_n),
    (POPS.inv_io_p, POPS.inv_io_n),
    (POPS.inv_pc_p, POPS.inv_pc_n),
    (POPS.error_p, POPS.error_n),
    (POPS.error_inv_p, POPS.error_inv_n),
    (POPS.feedback_p, POPS.feedback_n),
    (POPS.feedback_inv_p, POPS.feedback_inv_n),
    (POPS.motor_prediction_p, POPS.motor_prediction_n),
    (POPS.state_to_inv_p, POPS.state_to_inv_n),
    (POPS.fbk_smooth_p, POPS.fbk_smooth_n),
    (POPS.pred_p, POPS.pred_n),
]

POPS_SINGLE = [
    POPS.motor_commands,
    POPS.plan_to_inv,
    POPS.forw_bc,
    POPS.forw_glom,
    POPS.forw_goc,
    POPS.forw_grc,
    POPS.forw_mf,
    POPS.forw_sc,
    POPS.inv_bc,
    POPS.inv_glom,
    POPS.inv_goc,
    POPS.inv_grc,
    POPS.inv_mf,
    POPS.inv_sc,
]
