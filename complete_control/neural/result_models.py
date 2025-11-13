from pathlib import Path
from neural.CerebellumHandlerPopulations import CerebellumHandlerPopulationsRecordings
from neural.CerebellumPopulations import CerebellumPopulationsRecordings
from neural.ControllerPopulations import ControllerPopulationsRecordings
from pydantic import BaseModel


class NeuralResultManifest(BaseModel):
    controller: ControllerPopulationsRecordings
    cerebellum: CerebellumPopulationsRecordings | None
    cerebellum_handler: CerebellumHandlerPopulationsRecordings | None
    weights: list[Path] | None
    use_cerebellum: bool
