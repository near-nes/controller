from neural.CerebellumHandlerPopulations import CerebellumHandlerPopulationsRecordings
from neural.CerebellumPopulations import CerebellumPopulationsRecordings
from neural.ControllerPopulations import ControllerPopulationsRecordings
from pydantic import BaseModel


class NeuralResultManifest(BaseModel):
    controller: ControllerPopulationsRecordings
    cerebellum: CerebellumPopulationsRecordings
    cerebellum_handler: CerebellumHandlerPopulationsRecordings
    simulation_time: float
    dt: float
