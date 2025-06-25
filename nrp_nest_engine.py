import numpy
import nest
import os


import json

####### NETWORK SETUP
# Load parameters from file
f = open('new_params.json')
params = json.load(f)
f.close()

mc_params = params["modules"]["motor_cortex"]
plan_params = params["modules"]["planner"]
pops_params = params["pops"]
conn_params = params["connections"]

# nest.set_verbosity("M_ERROR")

res = 0.1 #[ms]
time_span = 1000.0 #[ms]
n_trial = 1
time_vect  = numpy.linspace(0, time_span, num=int(numpy.round(time_span/res)), endpoint=True)

njt = 1
trj = numpy.loadtxt('trajectory.txt')
motorCommands=numpy.loadtxt('motor_commands.txt')

N = 50 # Number of neurons for each (sub-)population
nTot = 2*N*njt # Total number of neurons (one positive and one negative population for each DOF)

nest.ResetKernel()
nest.SetKernelStatus({"resolution": res})

### Install NESTML-generated module
nest.Install("custom_stdp_module")

### PLANNER: create and initialize the Planner population
# Input: target --> minimum jerk trajectory
# Output: spikes (firing rate proportional to elbow angle)
for i in range(njt):
    planner_p = nest.Create("tracking_neuron_nestml", n=N, params={"kp": plan_params["kp"], "base_rate": plan_params["base_rate"], "pos": True, "traj": trj, "simulation_steps": len(trj)})

    planner_n = nest.Create("tracking_neuron_nestml", n=N, params={"kp": plan_params["kp"], "base_rate": plan_params["base_rate"], "pos": False, "traj": trj, "simulation_steps": len(trj)})


### FEEDFORWARD MOTOR CORTEX: create and initialize the Motor cortex populationù
# Input: target --> double derivative + inverse dynamics --> torque to be applied to elbow joint (motor command)
# Output: spikes (firing rate proportional to torque)
for i in range(njt):
    motor_p = nest.Create("tracking_neuron_nestml", n=N, params={"kp":mc_params["ffwd_kp"], 'base_rate':mc_params['ffwd_base_rate'], 'pos': True, 'traj': motorCommands, 'simulation_steps': len(motorCommands)})

    motor_n = nest.Create("tracking_neuron_nestml", n=N, params={'kp':mc_params["ffwd_kp"], 'base_rate':mc_params['ffwd_base_rate'], 'pos': False, 'traj': motorCommands, 'simulation_steps': len(motorCommands)})

### BRAINSTEM
# Input: spikes from FFWD motor cortex
# Output: smoothed profile of firing rate over time
for j in range(njt):
    # Positive neurons
    brainstem_p = nest.Create ("basic_neuron_nestml", N)
    nest.SetStatus(brainstem_p, {"kp": pops_params["brain_stem"]["kp"], "pos": True, "buffer_size": pops_params["brain_stem"]["buffer_size"], "base_rate": pops_params["brain_stem"]["base_rate"], "simulation_steps": len(time_vect)})
    # Negative neurons
    brainstem_n = nest.Create ("basic_neuron_nestml", N)
    nest.SetStatus(brainstem_n, {"kp": pops_params["brain_stem"]["kp"], "pos": False, "buffer_size": pops_params["brain_stem"]["buffer_size"], "base_rate": pops_params["brain_stem"]["base_rate"], "simulation_steps": len(time_vect)})

### Connections between FFWD MC and brainstem
for j in range(njt):
    nest.Connect(motor_p, brainstem_p, "all_to_all", {"weight": conn_params["mc_out_brain_stem"]["weight"], "delay": conn_params["mc_out_brain_stem"]["delay"]})

    nest.Connect(motor_n ,brainstem_n, "all_to_all", {"weight": -conn_params["mc_out_brain_stem"]["weight"], "delay": conn_params["mc_out_brain_stem"]["delay"]})

### DEVICES
spikedetector_planner_pos = nest.Create("spike_recorder", params={"label": "Planner pos"})
spikedetector_planner_neg = nest.Create("spike_recorder", params={"label": "Planner neg"})

spikedetector_brain_stem_pos = nest.Create("spike_recorder", params={"label": "Brain stem pos"})
spikedetector_brain_stem_neg = nest.Create("spike_recorder", params={"label": "Brain stem neg"})

spikedetector_motor_cortex_pos = nest.Create("spike_recorder", params={"label": "Motor cortex pos"})
spikedetector_motor_cortex_neg = nest.Create("spike_recorder", params={"label": "Motor cortex neg"})

nest.Connect(planner_p, spikedetector_planner_pos)
nest.Connect(planner_n, spikedetector_planner_neg)

nest.Connect(brainstem_p, spikedetector_brain_stem_pos)
nest.Connect(brainstem_n, spikedetector_brain_stem_neg)

nest.Connect(motor_p, spikedetector_motor_cortex_pos)
nest.Connect(motor_n, spikedetector_motor_cortex_neg)


# These variables are bound to NRP DataPacks
populations = {
    'spikedetector_brain_stem_pos': spikedetector_brain_stem_pos,
    'spikedetector_brain_stem_neg': spikedetector_brain_stem_neg
}
