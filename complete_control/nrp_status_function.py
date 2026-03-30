from nrp_core import *
from nrp_core.data.nrp_protobuf import *
from nrp_core.data.nrp_json import JsonRawData


@EngineDataPack(
    keyword="joint_pos_rad", id=DataPackIdentifier("joint_pos_rad", "bullet_simulator")
)
@StatusFunction()
def status_function(joint_pos_rad):

    ret = JsonRawData()
    ret.data["test_data"] = joint_pos_rad.data.value

    # can be get from run_loop function:
    return True, [ret]
