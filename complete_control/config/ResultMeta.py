from pathlib import Path
from pydantic import BaseModel

from config.paths import RunPaths
from config.MasterParams import MasterParams
from neural.result_models import NeuralResultManifest
from plant.plant_models import PlantPlotData


class ResultMeta(BaseModel):
    id: str
    parent: str
    neural: Path
    robotic: Path
    params: Path

    @classmethod
    def create(cls, params: MasterParams, **kwargs):
        return ResultMeta(
            id=params.run_id,
            parent="",
            neural=params.run_paths.neural_result,
            robotic=params.run_paths.robot_result,
            params=params.run_paths.params_json,
        )

    def save(self, paths: RunPaths) -> None:
        with open(paths.meta_result, "w") as f:
            f.write(self.model_dump_json(indent=2))

    class Config:
        arbitrary_types_allowed = True
