from nrp_core import *
from nrp_core.data.nrp_json import *


@EngineDataPack(
    keyword="positions", id=DataPackIdentifier("positions", "bullet_simulator")
)
@TransceiverFunction("nest_client")
def from_bullet(positions):
    position = JsonDataPack("positions", "nest_client")
    position.data["joint_pos_rad"] = positions.data["joint_pos_rad"]
    print(position)

    return [position]
