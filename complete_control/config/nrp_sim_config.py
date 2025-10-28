from pydantic import BaseModel
from typing import List


class EngineConfig(BaseModel):
    EngineType: str
    EngineName: str
    ServerAddress: str
    PythonFileName: str
    ProtobufPackages: List[str] = ["Wrappers", "NrpGenericProto"]
    EngineTimestep: float = 0.0001


class DataPackProcessingFunction(BaseModel):
    Name: str
    FileName: str


class SimulationConfig(BaseModel):
    SimulationName: str = "test_bullet"
    SimulationDescription: str = (
        "Launch a py_sim engine to run a Bullet simulation and a python engine to control the simulation"
    )
    SimulationTimeout: int = 1
    EngineConfigs: List[EngineConfig] = [
        EngineConfig(
            EngineType="python_grpc",
            EngineName="bullet_simulator",
            ServerAddress="0.0.0.0:1234",
            PythonFileName="complete_control/nrp_bullet_engine.py",
        ),
        EngineConfig(
            EngineType="python_grpc",
            EngineName="nest_client",
            ServerAddress="0.0.0.0:1235",
            PythonFileName="complete_control/nrp_neural_engine.py",
        ),
    ]
    DataPackProcessingFunctions: List[DataPackProcessingFunction] = [
        DataPackProcessingFunction(
            Name="to_bullet",
            FileName="complete_control/nrp_tf_from_nest_to_bullet.py",
        ),
        DataPackProcessingFunction(
            Name="from_bullet",
            FileName="complete_control/nrp_tf_from_bullet.py",
        ),
    ]
