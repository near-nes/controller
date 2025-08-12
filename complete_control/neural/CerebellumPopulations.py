from dataclasses import dataclass, field
from typing import List, Optional

from .population_view import PopView


@dataclass
class CerebellumPopulations:
    # === Forward Model Core Populations ===
    # Mossy Fibers (split for positive/negative or distinct inputs)
    forw_mf_view: Optional[PopView] = None
    # Add other specific MF views if inputs are more complex than simple p/n split

    # Granular Layer
    forw_glom_view: Optional[PopView] = None
    forw_grc_view: Optional[PopView] = None
    forw_goc_view: Optional[PopView] = None

    # Molecular Layer
    forw_pc_p_view: Optional[PopView] = None  # Purkinje Cells (e.g., positive channel)
    forw_pc_n_view: Optional[PopView] = None  # Purkinje Cells (e.g., negative channel)
    forw_bc_view: Optional[PopView] = None  # Basket Cells
    forw_sc_view: Optional[PopView] = None  # Stellate Cells

    # Inferior Olive
    forw_io_p_view: Optional[PopView] = None
    forw_io_n_view: Optional[PopView] = None

    # Deep Cerebellar Nuclei
    forw_dcnp_p_view: Optional[PopView] = None  # DCN projecting (e.g., positive)
    forw_dcnp_n_view: Optional[PopView] = None  # DCN projecting (e.g., negative)
    # forw_dcni_p_view: Optional[PopView] = None # DCN interneuron (if recorded/used)
    # forw_dcni_n_view: Optional[PopView] = None # DCN interneuron (if recorded/used)

    # === Inverse Model Core Populations ===
    # Mossy Fibers
    inv_mf_view: Optional[PopView] = None

    # Granular Layer
    inv_glom_view: Optional[PopView] = None
    inv_grc_view: Optional[PopView] = None
    inv_goc_view: Optional[PopView] = None

    # Molecular Layer
    inv_pc_p_view: Optional[PopView] = None
    inv_pc_n_view: Optional[PopView] = None
    inv_bc_view: Optional[PopView] = None
    inv_sc_view: Optional[PopView] = None

    # Inferior Olive
    inv_io_p_view: Optional[PopView] = None
    inv_io_n_view: Optional[PopView] = None

    # Deep Cerebellar Nuclei
    inv_dcnp_p_view: Optional[PopView] = None
    inv_dcnp_n_view: Optional[PopView] = None
    # inv_dcni_p_view: Optional[PopView] = None
    # inv_dcni_n_view: Optional[PopView] = None

    def get_all_views(self) -> List[PopView]:
        views = []
        for pop_field_name in self.__dataclass_fields__:
            view = getattr(self, pop_field_name)
            if isinstance(view, PopView):
                views.append(view)
        return views
