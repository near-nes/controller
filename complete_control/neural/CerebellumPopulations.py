from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from complete_control.neural.neural_models import (
    RecordingManifest,
    convert_to_recording,
)

from .population_view import PopView

T = TypeVar("T")


class CerebellumPopulationsGeneric(BaseModel, Generic[T]):
    # === Forward Model Core Populations ===
    # Mossy Fibers (split for positive/negative or distinct inputs)
    forw_mf_view: Optional[T] = None

    # Granular Layer
    forw_glom_view: Optional[T] = None
    forw_grc_view: Optional[T] = None
    forw_goc_view: Optional[T] = None

    # Molecular Layer
    forw_pc_p_view: Optional[T] = None  # Purkinje Cells
    forw_pc_n_view: Optional[T] = None
    forw_bc_view: Optional[T] = None  # Basket Cells
    forw_sc_view: Optional[T] = None  # Stellate Cells

    # Inferior Olive
    forw_io_p_view: Optional[T] = None
    forw_io_n_view: Optional[T] = None

    # Deep Cerebellar Nuclei
    forw_dcnp_p_view: Optional[T] = None  # DCN projecting
    forw_dcnp_n_view: Optional[T] = None

    # === Inverse Model Core Populations ===
    # Mossy Fibers
    inv_mf_view: Optional[T] = None

    # Granular Layer
    inv_glom_view: Optional[T] = None
    inv_grc_view: Optional[T] = None
    inv_goc_view: Optional[T] = None

    # Molecular Layer
    inv_pc_p_view: Optional[T] = None
    inv_pc_n_view: Optional[T] = None
    inv_bc_view: Optional[T] = None
    inv_sc_view: Optional[T] = None

    # Inferior Olive
    inv_io_p_view: Optional[T] = None
    inv_io_n_view: Optional[T] = None

    # Deep Cerebellar Nuclei
    inv_dcnp_p_view: Optional[T] = None
    inv_dcnp_n_view: Optional[T] = None

    class Config:
        arbitrary_types_allowed = True


class CerebellumPopulationsRecordings(CerebellumPopulationsGeneric[RecordingManifest]):
    pass


class CerebellumPopulations(CerebellumPopulationsGeneric[PopView]):
    def to_recording(self, *args, **kwargs) -> CerebellumPopulationsRecordings:
        return convert_to_recording(
            self, CerebellumPopulationsRecordings, *args, **kwargs
        )

    def get_plastic_pairs(self) -> tuple[tuple[PopView, PopView]]:
        return (
            (self.forw_grc_view, self.forw_pc_p_view),
            (self.forw_grc_view, self.forw_pc_n_view),
            (self.inv_grc_view, self.inv_pc_p_view),
            (self.inv_grc_view, self.inv_pc_n_view),
        )
