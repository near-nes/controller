#!/usr/bin/env python3
import sys
import numpy as np
import time
import os
import music
import matplotlib.pyplot as plt

import json
from timeit import default_timer as timer
from datetime import timedelta

print(f"starting timer")
start = timer()

# Adjust env vars to be able to import the NESTML-generated module
ld_lib_path = os.environ.get("LD_LIBRARY_PATH", "")
new_path = ld_lib_path + ":" + "../nestml/target"
os.environ["LD_LIBRARY_PATH"] = new_path

# Import the module
import nest

# Just to get the following imports right!
sys.path.insert(1, "../")

from neural.motorcortex import MotorCortex
from planner import Planner
from neural.stateestimator import StateEstimator, StateEstimator_mass

# from cerebellum import Cerebellum
from population_view import plotPopulation, PopView

from settings import MusicCfg, Experiment, Simulation
import mpi4py
from mpi4py import MPI
import ctypes

ctypes.CDLL("libmpi.so", mode=ctypes.RTLD_GLOBAL)
import json
from data_handling import collapse_files, add_entry
import random
from settings import SEED

nest.ResetKernel()
nest.rng_seed = SEED
random.seed = SEED
np.random.seed(SEED)
saveFig = True
ScatterPlot = False

# Opening JSON file to get parameters
f = open("new_params.json")
params = json.load(f)
f.close()

mc_params = params["modules"]["motor_cortex"]
plan_params = params["modules"]["planner"]
spine_params = params["modules"]["spine"]
state_params = params["modules"]["state"]
state_se_params = params["modules"]["state_se"]
pops_params = params["pops"]
conn_params = params["connections"]

# %%  SIMULATION
from pathlib import Path

exp = Experiment()
sim = Simulation()
pathFig = exp.pathFig
pathData = exp.pathData + "nest/"
for root, dirs, files in os.walk(exp.pathData):
    if root != exp.pathData:
        for file in files:
            print(f"removing {file}")
            Path(os.path.join(root, file)).unlink(missing_ok=True)
res = 0.1  # [ms]

trj = np.loadtxt("trajectory.txt")
motorCommands = np.loadtxt("motor_commands.txt")

assert len(trj) == len(motorCommands)
n_trials = sim.n_trials
time_span = sim.timeMax + sim.timeWait
time_vect = np.linspace(0, time_span, num=int(np.round(time_span / res)), endpoint=True)

total_time = time_span * n_trials
total_time_vect = np.linspace(
    0, total_time, num=int(np.round(total_time / res)), endpoint=True
)
njt = 1

assert len(trj) == len(total_time_vect)
N = 50  # Number of neurons for each (sub-)population
nTot = (
    2 * N * njt
)  # Total number of neurons (one positive and one negative population for each DOF)

# nest.ResetKernel()
nest.SetKernelStatus({"resolution": res})
nest.SetKernelStatus({"overwrite_files": True})
nest.SetKernelStatus({"data_path": pathData})

# # Cerebellum
cereb_controlled_joint = 0  # x = 0, y = 1

# Install the module containing neurons for planner and motor cortex
nest.Install("controller_module")
#### Planner
print("init planner")
print("--- Original Simulation Planner Init ---")
print(f"N: {N}")
print(f"njt: {njt}")
print(
    f"total_time_vect len: {len(total_time_vect)}, start: {total_time_vect[0]:.2f}, end: {total_time_vect[-1]:.2f}, res: {res}"
)
print(f"trj shape: {trj.shape}, start: {trj[0]:.4f}, end: {trj[-1]:.4f}")
print(f"pathData: {pathData}")
print(f"plan_params['kpl']: {plan_params['kpl']}")
print(f"plan_params['base_rate']: {plan_params['base_rate']}")
print(f"plan_params['kp']: {plan_params['kp']}")
planner = Planner(
    N,
    njt,
    total_time_vect,
    trj,
    pathData,
    plan_params["kpl"],
    plan_params["base_rate"],
    plan_params["kp"],
)

#### Motor cortex
print("init mc")
preciseControl = False  # Precise or approximated ffwd commands?
print("--- Original Simulation MotorCortex Init ---")
print(f"N: {N}")
print(f"njt: {njt}")
print(
    f"total_time_vect len: {len(total_time_vect)}, start: {total_time_vect[0]:.2f}, end: {total_time_vect[-1]:.2f}, res: {res}"
)
print(
    f"motorCommands shape: {motorCommands.shape}, start: {motorCommands[0]:.4f}, end: {motorCommands[-1]:.4f}"
)
print(f"mc_params: {mc_params}")
mc = MotorCortex(N, njt, total_time_vect, motorCommands, **mc_params)

#### State Estimator
print("init state")
buf_sz = state_params["buffer_size"]
additional_state_params = {
    "N_fbk": N,
    "N_pred": N,
    "fbk_bf_size": N * int(buf_sz / res),
    "pred_bf_size": N * int(buf_sz / res),
    "time_wait": sim.timeWait,
    "time_trial": sim.timeMax + sim.timeWait,
}
state_params.update(additional_state_params)
print("--- Original Simulation StateEstimator Init ---")
print(f"N: {N}")
print(f"njt: {njt}")
print(
    f"total_time_vect len: {len(total_time_vect)}, start: {total_time_vect[0]:.2f}, end: {total_time_vect[-1]:.2f}, res: {res}"
)
print(f"state_params for StateEstimator_mass: {state_params}")
stEst = StateEstimator_mass(N, njt, total_time_vect, **state_params)

# %% SPINAL CORD ########################

delay_fbk = params["modules"]["spine"]["fbk_delay"]
wgt_sensNeur_spine = params["modules"]["spine"]["wgt_sensNeur_spine"]

#### Sensory feedback (Parrot neurons on Sensory neurons)
sn_p = []
sn_n = []

for j in range(njt):
    # Positive neurons
    tmp_p = nest.Create("parrot_neuron", N)
    sn_p.append(PopView(tmp_p, total_time_vect, to_file=True, label="sn_p"))
    # Negative neurons
    tmp_n = nest.Create("parrot_neuron", N)
    sn_n.append(PopView(tmp_n, total_time_vect, to_file=True, label="sn_n"))

# %% State estimator #######
# Scale the cerebellar prediction up to 1000 Hz
# in order to have firing rate suitable for the State estimator
# and all the other structures inside the control system
prediction_p = []
prediction_n = []
tmp_p = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_p,
    {
        "kp": pops_params["prediction"]["kp"],
        "pos": True,
        "buffer_size": pops_params["prediction"]["buffer_size"],
        "base_rate": pops_params["prediction"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)  # 5.5
prediction_p.append(PopView(tmp_p, total_time_vect, to_file=True, label="pred_p"))
tmp_n = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_n,
    {
        "kp": pops_params["prediction"]["kp"],
        "pos": False,
        "buffer_size": pops_params["prediction"]["buffer_size"],
        "base_rate": pops_params["prediction"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)  # 5.5
prediction_n.append(PopView(tmp_n, total_time_vect, to_file=True, label="pred_n"))

wgt_fbk_sm_state = params["connections"]["fbk_smoothed_state"]["weight"]


for j in range(njt):
    """"""
    if j == cereb_controlled_joint:
        # Modify variability sensory feedback ("smoothed")
        fbk_smoothed_p = nest.Create("basic_neuron_nestml", N)
        nest.SetStatus(
            fbk_smoothed_p,
            {
                "kp": pops_params["fbk_smoothed"]["kp"],
                "pos": True,
                "buffer_size": pops_params["fbk_smoothed"]["buffer_size"],
                "base_rate": pops_params["fbk_smoothed"]["base_rate"],
                "simulation_steps": len(total_time_vect),
            },
        )
        fbk_smoothed_n = nest.Create("basic_neuron_nestml", N)
        nest.SetStatus(
            fbk_smoothed_n,
            {
                "kp": pops_params["fbk_smoothed"]["kp"],
                "pos": False,
                "buffer_size": pops_params["fbk_smoothed"]["buffer_size"],
                "base_rate": pops_params["fbk_smoothed"]["base_rate"],
                "simulation_steps": len(total_time_vect),
            },
        )

        nest.Connect(
            sn_p[j].pop,
            fbk_smoothed_p,
            "all_to_all",
            syn_spec={
                "weight": conn_params["sn_fbk_smoothed"]["weight"],
                "delay": conn_params["sn_fbk_smoothed"]["delay"],
            },
        )

        nest.Connect(
            sn_n[j].pop,
            fbk_smoothed_n,
            "all_to_all",
            syn_spec={
                "weight": -conn_params["sn_fbk_smoothed"]["weight"],
                "delay": conn_params["sn_fbk_smoothed"]["delay"],
            },
        )

        # Positive neurons
        for i, pre in enumerate(fbk_smoothed_p):
            for k, post in enumerate(stEst.pops_p[j].pop):
                nest.Connect(
                    pre,
                    post,
                    "one_to_one",
                    syn_spec={"weight": wgt_fbk_sm_state, "receptor_type": i + 1},
                )

        for i, pre in enumerate(prediction_p[0].pop):
            for k, post in enumerate(stEst.pops_p[j].pop):
                nest.Connect(
                    pre,
                    post,
                    "one_to_one",
                    syn_spec={"weight": 1.0, "receptor_type": i + 1 + N},
                )

        # Negative neurons
        for i, pre in enumerate(fbk_smoothed_n):
            for k, post in enumerate(stEst.pops_n[j].pop):
                nest.Connect(
                    pre,
                    post,
                    "one_to_one",
                    syn_spec={"weight": wgt_fbk_sm_state, "receptor_type": i + 1},
                )

        for i, pre in enumerate(prediction_n[0].pop):
            for k, post in enumerate(stEst.pops_n[j].pop):
                nest.Connect(
                    pre,
                    post,
                    "one_to_one",
                    syn_spec={"weight": 1.0, "receptor_type": i + 1 + N},
                )
    else:

        # Positive neurons
        # nest.Connect(sn_p[j].pop, stEst.pops_p[j].pop, "all_to_all", syn_spec=conn_params["sn_state"])
        for i, pre in enumerate(sn_p[j].pop):
            for k, post in enumerate(stEst.pops_p[j].pop):
                nest.Connect(
                    pre,
                    post,
                    "one_to_one",
                    syn_spec={
                        "weight": conn_params["sn_state"]["weight"],
                        "receptor_type": i + 1,
                    },
                )
        # Negative neurons

        for i, pre in enumerate(sn_n[j].pop):
            for k, post in enumerate(stEst.pops_n[j].pop):
                nest.Connect(
                    pre,
                    post,
                    "one_to_one",
                    syn_spec={
                        "weight": conn_params["sn_state"]["weight"],
                        "receptor_type": i + 1,
                    },
                )

print("init connections feedback")
"""
#%% CONNECTIONS
"""
#### Connection Planner - Motor Cortex feedback (excitatory)
wgt_plnr_mtxFbk = conn_params["planner_mc_fbk"]["weight"]


# Delay between planner and motor cortex feedback.
# It needs to compensate for the delay introduced by the state estimator
# delay_plnr_mtxFbk = brain.stEst_param["buf_sz"] # USE THIS WITH REAL STATE ESTIMATOR
delay_plnr_mtxFbk = conn_params["planner_mc_fbk"][
    "delay"
]  # USE THIS WITH "FAKE" STATE ESTIMATOR

for j in range(njt):
    planner.pops_p[j].connect(
        mc.fbk_p[j], rule="one_to_one", w=wgt_plnr_mtxFbk, d=delay_plnr_mtxFbk
    )
    planner.pops_p[j].connect(
        mc.fbk_n[j], rule="one_to_one", w=wgt_plnr_mtxFbk, d=delay_plnr_mtxFbk
    )
    planner.pops_n[j].connect(
        mc.fbk_p[j], rule="one_to_one", w=-wgt_plnr_mtxFbk, d=delay_plnr_mtxFbk
    )
    planner.pops_n[j].connect(
        mc.fbk_n[j], rule="one_to_one", w=-wgt_plnr_mtxFbk, d=delay_plnr_mtxFbk
    )

#### Connection State Estimator - Motor Cortex feedback (Inhibitory)
wgt_stEst_mtxFbk = conn_params["state_mc_fbk"]["weight"]


"""
nest.Connect(mc.out_p[cereb_controlled_joint].pop, motor_commands_p, "all_to_all", syn_spec={"weight": conn_params["mc_out_motor_commands"]["weight"], "delay": conn_params["mc_out_motor_commands"]["delay"]})
nest.Connect(mc.out_n[cereb_controlled_joint].pop, motor_commands_n, "all_to_all", syn_spec={"weight": -conn_params["mc_out_motor_commands"]["weight"], "delay": conn_params["mc_out_motor_commands"]["delay"]})
''
nest.Connect(motor_commands_p, cerebellum_forw.Nest_Mf[-n_forw:], {'rule': 'one_to_one'},syn_spec={'weight':1.0})
nest.Connect(motor_commands_n, cerebellum_forw.Nest_Mf[0:n_forw], {'rule': 'one_to_one'},syn_spec={'weight':1.0})#TODO add weight

# Scale the feedback signal to 0-60 Hz in order to be suitable for the cerebellum
feedback_p = nest.Create("diff_neuron", N)
nest.SetStatus(feedback_p, {"kp": pops_params["feedback"]["kp"], "pos": True, "buffer_size": pops_params["feedback"]["buffer_size"], "base_rate": pops_params["feedback"]["base_rate"]})
feedback_n = nest.Create("diff_neuron", N)
nest.SetStatus(feedback_n, {"kp": pops_params["feedback"]["kp"], "pos": False, "buffer_size": pops_params["feedback"]["buffer_size"], "base_rate": pops_params["feedback"]["base_rate"]})

nest.Connect(sn_p[cereb_controlled_joint].pop, feedback_p, 'all_to_all', syn_spec={"weight": conn_params["sn_fbk_smoothed"]["weight"], "delay": conn_params["sn_fbk_smoothed"]["delay"]})
nest.Connect(sn_n[cereb_controlled_joint].pop, feedback_n, 'all_to_all', syn_spec={"weight": -conn_params["sn_fbk_smoothed"]["weight"], "delay": conn_params["sn_fbk_smoothed"]["delay"]})
"""

# Connect state estimator (bayesian) to the Motor Cortex
for j in range(njt):
    nest.Connect(
        stEst.pops_p[j].pop,
        mc.fbk_p[j].pop,
        "one_to_one",
        {"weight": wgt_stEst_mtxFbk, "delay": res},
    )
    nest.Connect(
        stEst.pops_p[j].pop,
        mc.fbk_n[j].pop,
        "one_to_one",
        {"weight": wgt_stEst_mtxFbk, "delay": res},
    )
    nest.Connect(
        stEst.pops_n[j].pop,
        mc.fbk_p[j].pop,
        "one_to_one",
        {"weight": -wgt_stEst_mtxFbk, "delay": res},
    )
    nest.Connect(
        stEst.pops_n[j].pop,
        mc.fbk_n[j].pop,
        "one_to_one",
        {"weight": -wgt_stEst_mtxFbk, "delay": res},
    )

# BRAIN STEM
brain_stem_new_p = []
brain_stem_new_n = []


for j in range(njt):
    # Positive neurons
    tmp_p = nest.Create("basic_neuron_nestml", N)
    nest.SetStatus(
        tmp_p,
        {
            "kp": pops_params["brain_stem"]["kp"],
            "pos": True,
            "buffer_size": pops_params["brain_stem"]["buffer_size"],
            "base_rate": pops_params["brain_stem"]["base_rate"],
            "simulation_steps": len(total_time_vect),
        },
    )
    brain_stem_new_p.append(
        PopView(tmp_p, total_time_vect, to_file=True, label="brainstem_p")
    )
    # Negative neurons
    tmp_n = nest.Create("basic_neuron_nestml", N)
    nest.SetStatus(
        tmp_n,
        {
            "kp": pops_params["brain_stem"]["kp"],
            "pos": False,
            "buffer_size": pops_params["brain_stem"]["buffer_size"],
            "base_rate": pops_params["brain_stem"]["base_rate"],
            "simulation_steps": len(total_time_vect),
        },
    )
    brain_stem_new_n.append(
        PopView(tmp_n, total_time_vect, to_file=True, label="brainstem_n")
    )


for j in range(njt):
    nest.Connect(
        mc.out_p[j].pop,
        brain_stem_new_p[j].pop,
        "all_to_all",
        {
            "weight": conn_params["mc_out_brain_stem"]["weight"],
            "delay": conn_params["mc_out_brain_stem"]["delay"],
        },
    )
    # nest.Connect(stEst.pops_p[j].pop,mc.fbk_n[j].pop, "one_to_one", {"weight": wgt_stEst_mtxFbk, "delay": res})
    # nest.Connect(stEst.pops_n[j].pop,mc.fbk_p[j].pop, "one_to_one", {"weight": -wgt_stEst_mtxFbk, "delay": res})
    nest.Connect(
        mc.out_n[j].pop,
        brain_stem_new_n[j].pop,
        "all_to_all",
        {
            "weight": -conn_params["mc_out_brain_stem"]["weight"],
            "delay": conn_params["mc_out_brain_stem"]["delay"],
        },
    )

"""
# feedback from sensory
feedback_inv_p = nest.Create("diff_neuron", N)
nest.SetStatus(feedback_inv_p, {"kp": pops_params["feedback_inv"]["kp"], "pos": True, "buffer_size": pops_params["feedback_inv"]["buffer_size"], "base_rate": pops_params["feedback_inv"]["base_rate"]})
feedback_inv_n = nest.Create("diff_neuron", N)
nest.SetStatus(feedback_inv_n, {"kp": pops_params["feedback_inv"]["kp"], "pos": False, "buffer_size": pops_params["feedback_inv"]["buffer_size"], "base_rate": pops_params["feedback_inv"]["base_rate"]})
"""

# %% MUSIC CONFIG

msc = MusicCfg()

#### MUSIC output port (with nTot channels)
proxy_out = nest.Create("music_event_out_proxy", 1, params={"port_name": "mot_cmd_out"})

ii = 0
for j in range(njt):
    for i, n in enumerate(brain_stem_new_p[j].pop):
        nest.Connect(n, proxy_out, "one_to_one", {"music_channel": ii})
        ii = ii + 1
    for i, n in enumerate(brain_stem_new_n[j].pop):
        nest.Connect(n, proxy_out, "one_to_one", {"music_channel": ii})
        ii = ii + 1


#### MUSIC input ports (nTot ports with one channel each)
proxy_in = nest.Create("music_event_in_proxy", nTot, params={"port_name": "fbk_in"})
for i, n in enumerate(proxy_in):
    nest.SetStatus(n, {"music_channel": i})

# Divide channels based on function (using channel order)
for j in range(njt):
    # Check joint: only joint controlled by the cerebellum can be affected by delay
    if j == cereb_controlled_joint:
        delay = delay_fbk
    else:
        delay = 0.1

    #### Positive channels
    idxSt_p = 2 * N * j
    idxEd_p = idxSt_p + N
    nest.Connect(
        proxy_in[idxSt_p:idxEd_p],
        sn_p[j].pop,
        "one_to_one",
        {"weight": wgt_sensNeur_spine, "delay": delay},
    )
    #### Negative channels
    idxSt_n = idxEd_p
    idxEd_n = idxSt_n + N
    nest.Connect(
        proxy_in[idxSt_n:idxEd_n],
        sn_n[j].pop,
        "one_to_one",
        {"weight": wgt_sensNeur_spine, "delay": delay},
    )

# We need to tell MUSIC, through NEST, that it's OK (due to the delay)
# to deliver spikes a bit late. This is what makes the loop possible.
nest.SetAcceptableLatency("fbk_in", 0.1 - msc.const)

###################### Extra Spikedetectors ######################

spikedetector_fbk_pos = nest.Create("spike_recorder", params={"label": "Feedback pos"})
spikedetector_fbk_neg = nest.Create("spike_recorder", params={"label": "Feedback neg"})

"""
spikedetector_fbk_inv_pos = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback inv pos"})
spikedetector_fbk_inv_neg = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback inv neg"})

spikedetector_fbk_cereb_pos = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback cerebellum pos"})
spikedetector_fbk_cereb_neg = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback cerebellum neg"})
spikedetector_io_forw_input_pos = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Input inferior Olive Forw pos"})
spikedetector_io_forw_input_neg = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Input inferior Olive Forw neg"})

spikedetector_io_inv_input_pos = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Input inferior Olive Inv pos"})
spikedetector_io_inv_input_neg = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Input inferior Olive Inv neg"})
"""
spikedetector_stEst_pos = nest.Create(
    "spike_recorder", params={"label": "State estimator pos"}
)
spikedetector_stEst_neg = nest.Create(
    "spike_recorder", params={"label": "State estimator neg"}
)

spikedetector_planner_pos = nest.Create(
    "spike_recorder", params={"label": "Planner pos"}
)
spikedetector_planner_neg = nest.Create(
    "spike_recorder", params={"label": "Planner neg"}
)

# spikedetector_pred_pos = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Cereb pred pos"})
# spikedetector_pred_neg = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Cereb pred neg"})
# spikedetector_motor_pred_pos = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Cereb motor pred pos"})
# spikedetector_motor_pred_neg = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "Cereb motor pred neg"})
# spikedetector_stEst_max_pos = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "State estimator Max pos"})
# spikedetector_stEst_max_neg = nest.Create("spike_recorder", params={"withgid": True,"withtime": True, "to_file": True, "label": "State estimator Max neg"})
spikedetector_fbk_smoothed_pos = nest.Create(
    "spike_recorder", params={"label": "Feedback smoothed pos"}
)
spikedetector_fbk_smoothed_neg = nest.Create(
    "spike_recorder", params={"label": "Feedback smoothed neg"}
)

spikedetector_brain_stem_pos = nest.Create(
    "spike_recorder", params={"label": "Brain stem pos"}
)
spikedetector_brain_stem_neg = nest.Create(
    "spike_recorder", params={"label": "Brain stem neg"}
)

nest.Connect(brain_stem_new_p[j].pop, spikedetector_brain_stem_pos)
nest.Connect(brain_stem_new_n[j].pop, spikedetector_brain_stem_neg)

nest.Connect(fbk_smoothed_p, spikedetector_fbk_smoothed_pos)


nest.Connect(sn_p[cereb_controlled_joint].pop, spikedetector_fbk_pos)
nest.Connect(sn_n[cereb_controlled_joint].pop, spikedetector_fbk_neg)
# nest.Connect(feedback_p, spikedetector_fbk_cereb_pos)
# nest.Connect(feedback_n, spikedetector_fbk_cereb_neg)

nest.Connect(planner.pops_p[cereb_controlled_joint].pop, spikedetector_planner_pos)
nest.Connect(planner.pops_n[cereb_controlled_joint].pop, spikedetector_planner_neg)
"""
nest.Connect(stEst.pops_p[cereb_controlled_joint].pop, spikedetector_stEst_max_pos)
nest.Connect(stEst.pops_n[cereb_controlled_joint].pop, spikedetector_stEst_max_neg)
"""


###################### SIMULATE ######################
"""
# Disable Cerebellar prediction in State estimation 
conns_pos_forw = nest.GetConnections(source = prediction_p, target = stEst.pops_p[cereb_controlled_joint].pop)
conns_neg_forw = nest.GetConnections(source = prediction_n, target = stEst.pops_n[cereb_controlled_joint].pop)

# set connection to zero
if cerebellum_application_forw != 0:
    nest.SetStatus(conns_pos_forw, {"weight": 0.0})
    nest.SetStatus(conns_neg_forw, {"weight": 0.0})
"""

time_network = timedelta(seconds=timer() - start)

# %% SIMULATE ######################
# nest.SetKernelStatus({"data_path": pthDat})
# total_len = int(time_span + time_pause)
names = exp.names
pops = [
    planner.pops_p,
    planner.pops_n,
    mc.ffwd_p,
    mc.ffwd_n,
    mc.fbk_p,
    mc.fbk_n,
    mc.out_p,
    mc.out_n,
    brain_stem_new_p,
    brain_stem_new_n,
    sn_p,
    sn_n,
    prediction_p,
    prediction_n,
    stEst.pops_p,
    stEst.pops_n,
]

total_len = int(time_span)

print(nest.GetNodes())


for trial in range(n_trials):
    if mpi4py.MPI.COMM_WORLD.rank == 0:
        print("Simulating trial {} lasting {} ms".format(trial + 1, total_len))
    nest.Simulate(total_len)
    collapse_files(pathData, names, pops, njt)
events_orig = nest.GetStatus(spikedetector_fbk_smoothed_pos, "events")[0]
times_orig = events_orig["times"]
senders_orig = events_orig["senders"]
print(f"--- Original fbk_smooth_p spikes ---")
print(f"Num spikes: {len(times_orig)}")
if len(times_orig) > 0:
    print(f"First spike time: {times_orig[0]}, sender: {senders_orig[0]}")
    print(f"Last spike time: {times_orig[-1]}, sender: {senders_orig[-1]}")
"""
if mpi4py.MPI.COMM_WORLD.rank == 0:
    choice = input("Save?")
    if choice == 'y':
        add_entry(exp)
"""

# Gather data


# add_entry(exp)


# %% PLOTTING
# Figure per la presentazione
# Planner + trajectory
if mpi4py.MPI.COMM_WORLD.rank == 0:
    lgd = ["theta"]
    # time_vect_paused = np.linspace(0, total_len*n_trial, num=int(np.round(total_len/res)), endpoint=True)
    time_vect_paused = total_time_vect
    print("planner")
    reference = [trj]
    legend = ["trajectory"]
    styles = ["k"]
    time_vecs = [time_vect_paused]
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            planner.pops_p[i],
            planner.pops_n[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Planner")
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/planner_"+lgd[i]+".png")
            plt.savefig(pathFig + "planner_" + lgd[i] + ".png")
    reference = [motorCommands]
    legend = ["motor commands"]

    print("mc ffwd")
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            mc.ffwd_p[i],
            mc.ffwd_n[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Mc ffwd")
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/mc_ffwd_"+lgd[i]+".png")
            plt.savefig(pathFig + "mc_ffwd_" + lgd[i] + ".png")

    bins_p, count_p, rate_p = planner.pops_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = planner.pops_n[0].computePSTH(time_vect_paused, 15)
    bins_stEst_p, count_stEst_p, rate_stEst_p = stEst.pops_p[0].computePSTH(
        time_vect_paused, 15
    )
    bins_stEst_n, count_stEst_n, rate_stEst_n = stEst.pops_n[0].computePSTH(
        time_vect_paused, 15
    )

    print("mc fbk")
    reference = [rate_p - rate_stEst_p, rate_n - rate_stEst_n]
    time_vecs = [bins_p[:-1], bins_n[:-1]]
    legend = ["diff_p", "diff_n"]
    styles = ["r--", "b--"]
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            mc.fbk_p[i],
            mc.fbk_n[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Mc fbk")
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/mc_fbk_"+lgd[i]+".png")
            plt.savefig(pathFig + "mc_fbk_" + lgd[i] + ".png")

    bins_p, count_p, rate_p = mc.ffwd_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = mc.ffwd_n[0].computePSTH(time_vect_paused, 15)
    bins_fbk_p, count_fbk_p, rate_fbk_p = mc.fbk_p[0].computePSTH(time_vect_paused, 15)
    bins_fbk_n, count_fbk_n, rate_fbk_n = mc.fbk_n[0].computePSTH(time_vect_paused, 15)
    print("mc out")
    reference = [rate_p + rate_fbk_p, rate_n + rate_fbk_n]
    time_vecs = [bins_p[:-1], bins_n[:-1]]
    legend = ["sum_p", "sum_n"]
    styles = ["r--", "b--"]
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            mc.out_p[i],
            mc.out_n[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Mc out")
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/mc_out_"+lgd[i]+".png")
            plt.savefig(pathFig + "mc_out_" + lgd[i] + ".png")

    bins_p, count_p, rate_p = mc.out_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = mc.out_n[0].computePSTH(time_vect_paused, 15)

    reference = [rate_p, rate_n]
    time_vecs = [bins_p[:-1], bins_n[:-1]]
    legend = ["out_p", "out_n"]
    styles = ["r", "b"]
    print("brainstem")
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            brain_stem_new_p[i],
            brain_stem_new_n[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Brainstem")
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/brainstem_"+lgd[i]+".png")
            plt.savefig(pathFig + "brainstem_" + lgd[i] + ".png")

    reference = []
    time_vecs = []
    legend = []
    styles = []
    print("sensory")
    print("prova: ", sn_n[i].total_ts)
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            sn_p[i],
            sn_n[i],
            reference,
            time_vecs,
            legend,
            styles,
            buffer_size=15,
        )
        plt.suptitle("Sensory")
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/sensory_"+lgd[i]+".png")
            plt.savefig(pathFig + "sensory_" + lgd[i] + ".png")

    bins_p, count_p, rate_p = sn_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = sn_n[0].computePSTH(time_vect_paused, 15)
    bins_pred_p, count_pred_p, rate_pred_p = prediction_p[0].computePSTH(
        time_vect_paused, 15
    )
    bins_pred_n, count_pred_n, rate_pred_n = prediction_n[0].computePSTH(
        time_vect_paused, 15
    )

    reference = [rate_p - rate_n, rate_pred_p - rate_pred_n]
    time_vecs = [bins_p[:-1], bins_n[:-1]]
    legend = ["net_sensory", "net_prediction"]
    styles = ["g--", "r--"]
    print("state")
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            stEst.pops_p[i],
            stEst.pops_n[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("State")
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "state_" + lgd[i] + ".png")
    print("net")
    bins_p, count_p, rate_p = planner.pops_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = planner.pops_n[0].computePSTH(time_vect_paused, 15)
    bins_stEst_p, count_stEst_p, rate_stEst_p = stEst.pops_p[0].computePSTH(
        time_vect_paused, 15
    )
    bins_stEst_n, count_stEst_n, rate_stEst_n = stEst.pops_n[0].computePSTH(
        time_vect_paused, 15
    )

    fig, ax = plt.subplots(2, 2)
    ax[0, 0].plot(bins_p[:-1], rate_p, label="planner pos")
    ax[0, 0].plot(bins_p[:-1], rate_stEst_p, label="state pos")
    ax[0, 0].set_xlabel("time")
    ax[0, 0].legend()
    ax[1, 0].plot(bins_n[:-1], rate_n, label="planner neg")
    ax[1, 0].plot(bins_n[:-1], rate_stEst_n, label="state neg")
    ax[1, 0].legend()
    ax[0, 1].plot(bins_p[:-1], rate_p - rate_stEst_p)
    ax[1, 1].plot(bins_n[:-1], rate_n - rate_stEst_n)

    plt.savefig("check_planner_state.png")


time_brainpy = timedelta(seconds=timer() - start)

print(f"final times:\nnetwork: {time_network}\nbrain.py: {time_brainpy}")
