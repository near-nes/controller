from pathlib import Path

from complete_control.config import paths
from complete_control.config.MasterParams import MasterParams
from complete_control.config.paths import RunPaths
from complete_control.neural.result_models import NeuralResultManifest
from complete_control.plant.plant_models import PlantPlotData
from pydantic import BaseModel


def extract_id(id: str):
    return id.partition("-")[0]


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
            parent=params.parent_id,
            neural=params.run_paths.neural_result,
            robotic=params.run_paths.robot_result,
            params=params.run_paths.params_json,
        )

    def load_neural(self) -> NeuralResultManifest:
        with open(self.neural, "r") as f:
            return NeuralResultManifest.model_validate_json(f.read())

    def load_robotic(self) -> PlantPlotData:
        with open(self.robotic, "r") as f:
            return PlantPlotData.model_validate_json(f.read())

    def load_params(self) -> MasterParams:
        with open(self.params, "r") as f:
            return MasterParams.model_validate_json(f.read())

    def save(self, paths: RunPaths) -> None:
        with open(paths.meta_result, "w") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def from_id(cls, id: str):
        id = extract_id(id)
        p = [i for i in paths.RUNS_DIR.glob(f"{id}*") if i.is_dir()]
        if len(p) != 1:
            raise ValueError(f"found {len(p)} result(s) for key='{id}'")

        rp = paths.RunPaths.from_run_id(p[0].name, create_if_not_present=False)
        with open(rp.meta_result, "r") as f:
            return ResultMeta.model_validate_json(f.read())

    class Config:
        arbitrary_types_allowed = True
