# This is calclated on NRP-Core side

from nrp_core import *
from nrp_core.data.nrp_protobuf import *


@EngineDataPack(
    keyword="control_cmd", id=DataPackIdentifier("control_cmd", "nest_client")
)
@TransceiverFunction("bullet_simulator")
def to_bullet(control_cmd):
    datapack = NrpGenericProtoArrayDoubleDataPack("control_cmd", "bullet_simulator")
    datapack.data.array.extend(control_cmd.data.array)

    return [datapack]
