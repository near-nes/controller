from typing import Generic, Optional, TypeVar

from neural.neural_models import PopulationSpikes, convert_to_recording
from pydantic import BaseModel

from .population_view import PopView

T = TypeVar("T")


class CerebellumPopulationsGeneric(BaseModel, Generic[T]):
    # === Forward Model Core Populations ===
    # Mossy Fibers (split for positive/negative or distinct inputs)
    forw_mf: Optional[T] = None

    # Granular Layer
    forw_glom: Optional[T] = None
    forw_grc: Optional[T] = None
    forw_goc: Optional[T] = None

    # Molecular Layer
    forw_pc_p: Optional[T] = None  # Purkinje Cells
    forw_pc_n: Optional[T] = None
    forw_bc: Optional[T] = None  # Basket Cells
    forw_sc: Optional[T] = None  # Stellate Cells

    # Inferior Olive
    forw_io_p: Optional[T] = None
    forw_io_n: Optional[T] = None

    # Deep Cerebellar Nuclei
    forw_dcnp_p: Optional[T] = None  # DCN projecting
    forw_dcnp_n: Optional[T] = None

    # === Inverse Model Core Populations ===
    # Mossy Fibers
    inv_mf: Optional[T] = None

    # Granular Layer
    inv_glom: Optional[T] = None
    inv_grc: Optional[T] = None
    inv_goc: Optional[T] = None

    # Molecular Layer
    inv_pc_p: Optional[T] = None
    inv_pc_n: Optional[T] = None
    inv_bc: Optional[T] = None
    inv_sc: Optional[T] = None

    # Inferior Olive
    inv_io_p: Optional[T] = None
    inv_io_n: Optional[T] = None

    # Deep Cerebellar Nuclei
    inv_dcnp_p: Optional[T] = None
    inv_dcnp_n: Optional[T] = None

    class Config:
        arbitrary_types_allowed = True


class CerebellumPopulationsRecordings(CerebellumPopulationsGeneric[PopulationSpikes]):
    pass


class CerebellumPopulations(CerebellumPopulationsGeneric[PopView]):
    def to_recording(self, *args, **kwargs) -> CerebellumPopulationsRecordings:
        return convert_to_recording(
            self, CerebellumPopulationsRecordings, *args, **kwargs
        )

    def __setattr__(self, name, value):
        # Auto-label PopView instances when assigned
        if isinstance(value, PopView) and name in CerebellumPopulations.model_fields:
            if value.label is None:
                # set value name as population label, trigger detector initialization
                value.label = name
        super().__setattr__(name, value)

    def get_plastic_pairs(self) -> tuple[tuple[PopView, PopView]]:
        return (
            (self.forw_grc, self.forw_pc_p),
            (self.forw_grc, self.forw_pc_n),
            (self.forw_grc, self.forw_sc),
            (self.forw_grc, self.forw_bc),
            (self.inv_grc, self.inv_pc_p),
            (self.inv_grc, self.inv_pc_n),
            (self.inv_grc, self.inv_sc),
            (self.inv_grc, self.inv_bc),
        )
