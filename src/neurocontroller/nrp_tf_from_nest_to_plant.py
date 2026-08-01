# This is calculated on NRP-Core side
# Transceiver function: NEST neural engine → Simulation engine (PyBullet/MuJoCo)

from nrp_core import *
from nrp_core.data.nrp_protobuf import *


@EngineDataPack(
    keyword="control_cmd", id=DataPackIdentifier("control_cmd", "nest_client")
)
@TransceiverFunction("simulation_engine")
def to_simulation_engine(control_cmd):
    datapack = NrpGenericProtoArrayDoubleDataPack("control_cmd", "simulation_engine")
    datapack.data.array.extend(control_cmd.data.array)

    return [datapack]
