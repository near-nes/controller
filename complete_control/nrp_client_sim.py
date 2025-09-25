import os
from datetime import datetime
# Get the current timestamp and format it as 'YYYYMMDD_HHMMSS'
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
# Set the environment variable
os.environ['EXEC_TIMESTAMP'] = timestamp
print(f"The environment variable 'EXEC_TIMESTAMP' has been set to: {os.environ.get('EXEC_TIMESTAMP')}")

from nrp_client import NrpCore
from nrp_protobuf import wrappers_pb2

nrp = NrpCore("0.0.0.0:5679", "/sim/controller/", "nrp_simulation_config_nest_docker_compose.json", log_output="log.log")

nrp.initialize()

data = wrappers_pb2.DoubleValue()
data.value = 123.456
nrp.set_proto_datapack("client_datapack", "bullet_simulator", data)

# Flag and trj are taken from the status_function return values 
Flag, trj = nrp.run_loop(10)
print(Flag)
print(trj)

nrp.shutdown()
