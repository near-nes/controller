from typing import Any, ClassVar, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel

from complete_control.neural.neural_models import ConvertToRecording, RecordingManifest

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


class CerebellumPopulations(CerebellumPopulationsGeneric[PopView], ConvertToRecording):
    RecordingClass: ClassVar[Type[CerebellumPopulationsRecordings]] = (
        CerebellumPopulationsRecordings
    )

    pass
