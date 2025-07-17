# This is calclated on NRP-Core side

from nrp_core import *
from nrp_core.data.nrp_json import *


@EngineDataPack(
    keyword="control_cmd", id=DataPackIdentifier("control_cmd", "nest_client")
)
@TransceiverFunction("bullet_simulator")
def to_bullet(control_cmd):
    rec_cmd = JsonDataPack("control_cmd", "bullet_simulator")
    print(control_cmd)
    print(rec_cmd)
    rec_cmd.data["rate_pos"] = control_cmd.data["rate_pos"]
    rec_cmd.data["rate_neg"] = control_cmd.data["rate_neg"]

    return [rec_cmd]
