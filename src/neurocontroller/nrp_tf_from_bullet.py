from nrp_core import *
from nrp_core.data.nrp_protobuf import *


@EngineDataPack(
    keyword="joint_pos_rad", id=DataPackIdentifier("joint_pos_rad", "bullet_simulator")
)
@TransceiverFunction("nest_client")
def from_bullet(joint_pos_rad):
    datapack = WrappersDoubleValueDataPack("joint_pos_rad", "nest_client")
    datapack.data.value = joint_pos_rad.data.value

    return [datapack]
