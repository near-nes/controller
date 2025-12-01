from pathlib import Path

from neural.CerebellumHandlerPopulations import CerebellumHandlerPopulationsRecordings
from neural.CerebellumPopulations import CerebellumPopulationsRecordings
from neural.ControllerPopulations import ControllerPopulationsRecordings
from neural.neural_models import PopulationSpikes
from pydantic import BaseModel


class NeuralResultManifest(BaseModel):
    controller: ControllerPopulationsRecordings
    cerebellum: CerebellumPopulationsRecordings | None
    cerebellum_handler: CerebellumHandlerPopulationsRecordings | None
    weights: list[Path] | list[list[Path]] | None
    use_cerebellum: bool

    def get_pop(self, pop_name: str | None) -> PopulationSpikes | None:
        if not pop_name:
            return None

        if hasattr(self.controller, pop_name):
            return getattr(self.controller, pop_name)

        if self.cerebellum and hasattr(self.cerebellum, pop_name):
            return getattr(self.cerebellum, pop_name)

        if self.cerebellum_handler and hasattr(self.cerebellum_handler, pop_name):
            return getattr(self.cerebellum_handler, pop_name)

        raise ValueError(f"Population '{pop_name}' not found in any result partition.")
