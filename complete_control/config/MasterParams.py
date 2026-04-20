import os
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field, computed_field

from .bsb_models import BSBConfigCopies, BSBConfigPaths
from .connection_params import ConnectionsParams
from .core_models import (
    BrainParams,
    ExperimentParams,
    MetaInfo,
    PlottingParams,
    SimulationParams,
)
from .module_params import ModuleContainerConfig
from .paths import RunPaths
from .population_params import PopulationsParams


class MasterParams(BaseModel):
    model_config: ClassVar = {
        "frozen": True,
        "arbitrary_types_allowed": True,
    }
    run_paths: RunPaths
    run_id: str
    parent_id: str

    USE_CEREBELLUM: bool = True
    GUI_PYBULLET: bool = False
    SAVE_WEIGHTS_CEREB: bool = True

    NJT: int = 1
    JOINTS_NO_CONTROL: int = 2
    plotting: PlottingParams = Field(default_factory=lambda: PlottingParams())
    simulation: SimulationParams = Field(default_factory=lambda: SimulationParams())
    experiment: ExperimentParams = Field(default_factory=lambda: ExperimentParams())
    brain: BrainParams = Field(default_factory=lambda: BrainParams())
    bsb_config_paths: BSBConfigPaths = Field(default_factory=lambda: BSBConfigPaths())

    @computed_field
    @property
    def meta(self) -> MetaInfo:
        return MetaInfo(run_id=self.run_paths.run.name)

    @computed_field
    @property
    def total_num_virtual_procs(self) -> int:
        return int(os.getenv("NPROC", 1))

    @computed_field
    @property
    # stores copies of yamls used
    def bsb_config_copies(self) -> BSBConfigCopies:
        return BSBConfigCopies.create(self.bsb_config_paths)

    modules: ModuleContainerConfig = Field(
        default_factory=lambda: ModuleContainerConfig()
    )
    populations: PopulationsParams = Field(default_factory=lambda: PopulationsParams())
    connections: ConnectionsParams = Field(default_factory=lambda: ConnectionsParams())

    def save_to_json(self, filepath: Path, indent: int = 2) -> None:
        """Serializes the MasterConfig instance to a JSON file."""
        with open(filepath, "w") as f:
            f.write(self.model_dump_json(indent=indent))

    @classmethod
    def from_runpaths(cls, run_paths: RunPaths, parent_id: str, **kwargs):
        return MasterParams(
            run_paths=run_paths,
            run_id=run_paths.run.name,
            parent_id=parent_id,
            **kwargs
        )
