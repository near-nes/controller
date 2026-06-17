from typing import List

from pydantic import BaseModel, computed_field

from . import MasterParams


class EngineConfig(BaseModel):
    EngineType: str
    EngineName: str
    ServerAddress: str
    PythonFileName: str
    ProtobufPackages: List[str] = ["Wrappers", "NrpGenericProto"]
    EngineTimestep: float = 0.001  # change here according to res


class DataPackProcessingFunction(BaseModel):
    Name: str
    FileName: str


class SimulationConfig(BaseModel):
    SimulationEngine: str
    SimulationTimeout: float

    @computed_field
    @property
    def SimulationName(self) -> str:
        return "test_" + self.SimulationEngine

    @computed_field
    @property
    def SimulationDescription(self) -> str:
        return "Launch a py_sim engine to run a" + self.SimulationEngine + " simulation and a python engine to control the simulation"

    @computed_field
    @property
    def EngineConfigs(self) -> List[EngineConfig]:
        return [
            EngineConfig(
                EngineType="python_grpc",
                EngineName=self.SimulationEngine + "_simulator",
                ServerAddress="0.0.0.0:1234",
                PythonFileName="src/neurocontroller/nrp_" + self.SimulationEngine + "_engine.py",
            ),
            EngineConfig(
                EngineType="python_grpc",
                EngineName="nest_client",
                ServerAddress="0.0.0.0:1235",
                PythonFileName="src/neurocontroller/nrp_neural_engine.py",
            )
        ]

    @computed_field
    @property
    def DataPackProcessingFunctions(self) -> List[DataPackProcessingFunction]:
        return [
            DataPackProcessingFunction(
                Name="to_" + self.SimulationEngine,
                FileName="src/neurocontroller/nrp_tf_from_nest_to_" + self.SimulationEngine + ".py",
            ),
            DataPackProcessingFunction(
                Name="from_" + self.SimulationEngine,
                FileName="src/neurocontroller/nrp_tf_from_" + self.SimulationEngine + ".py",
            ),
        ]

    @classmethod
    def from_masterparams(cls, mp: MasterParams, **kwargs):
        return SimulationConfig(
            SimulationTimeout=mp.simulation.duration_ms / 1000,
            SimulationEngine=mp.simulation.engine,
            **kwargs
        )
