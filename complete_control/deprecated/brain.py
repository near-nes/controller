#!/usr/bin/env python3
import json
import os
import time
from datetime import timedelta
from timeit import default_timer as timer

import matplotlib.pyplot as plt
import mpi4py
import music
import nest
import numpy as np
from data_handling import add_entry, collapse_files
from settings import Brain, Experiment, MusicCfg, Simulation

import trajectories as tj
from neural.Cerebellum import Cerebellum
from neural.motorcortex import MotorCortex
from planner import Planner
from population_view import PopView, plotPopulation, plotPopulation_diff
from neural.stateestimator import StateEstimator, StateEstimator_mass

start = timer()

saveFig = True
ScatterPlot = False
SHOW = False

with open("new_params.json") as f:
    params = json.load(f)

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
pathFig = exp.pathFig
pathData = exp.pathData + "nest/"
for root, dirs, files in os.walk(exp.pathData):
    if root != exp.pathData:
        for file in files:
            print(f"removing {file}")
            Path(os.path.join(root, file)).unlink(missing_ok=True)

sim = Simulation()
trj = np.loadtxt("trajectory.txt")
motorCommands = np.loadtxt("motor_commands.txt")
assert len(trj) == len(motorCommands)

res = sim.resolution
time_span = sim.timeMax + sim.timeWait
n_trials = sim.n_trials
time_vect = np.linspace(0, time_span, num=int(np.round(time_span / res)), endpoint=True)

total_time = time_span * n_trials
total_time_vect = np.linspace(
    0, total_time, num=int(np.round(total_time / res)), endpoint=True
)
assert len(trj) == len(total_time_vect)
njt = exp.dynSys.numVariables()
# nest.ResetKernel()
# nest.Install("controller_module")
# Randomize
msd = int(time.time() * 1000.0)
N_vp = nest.GetKernelStatus(["total_num_virtual_procs"])[0]
# nest.SetKernelStatus({'rng_seeds' : range(msd+N_vp+1, msd+2*N_vp+1)})


# %% BRAIN ########################
print("init brain")
brain = Brain()
# Number of neurons
N = brain.nNeurPop  # For each subpopulation positive/negative
nTot = 2 * N * njt  # Total number of neurons


cereb_controlled_joint = brain.cerebellum_controlled_joint
# Trial at which cerebellum is connected to StateEstimator
cerebellum_application_forw = exp.cerebellum_application_forw
# Trial at which cerebellum is connected to StateEstimator
cerebellum_application_inv = exp.cerebellum_application_inv

filename_h5 = brain.filename_h5
filename_config = brain.filename_config
cerebellum = Cerebellum(sim, exp, filename_h5, filename_config)
print("finished cerebellum")
time_cerebellum = timedelta(seconds=timer() - start)

N_mossy_forw = int(len(cerebellum.forw_Nest_Mf) / 2)
print(N_mossy_forw)
N_mossy_inv = int(len(cerebellum.inv_Nest_Mf) / 2)
print(N_mossy_inv)

# Make "external" cerebellar populations into PopView objects
forw_Nest_Mf_plus = [
    PopView(
        cerebellum.forw_Nest_Mf[-N_mossy_forw:],
        total_time_vect,
        to_file=True,
        label="forw_mf_plus",
    )
]
forw_Nest_Mf_minus = [
    PopView(
        cerebellum.forw_Nest_Mf[0:N_mossy_forw],
        total_time_vect,
        to_file=True,
        label="forw_mf_minus",
    )
]
forw_DCNp_plus = [
    PopView(
        cerebellum.forw_N_DCNp_plus,
        total_time_vect,
        to_file=True,
        label="forw_dcnp+",
    )
]
forw_DCNp_minus = [
    PopView(
        cerebellum.forw_N_DCNp_minus,
        total_time_vect,
        to_file=True,
        label="forw_dcnp-",
    )
]
forw_IO_plus = [
    PopView(
        cerebellum.forw_N_IO_plus,
        total_time_vect,
        to_file=True,
        label="forw_io+",
    )
]
forw_IO_minus = [
    PopView(
        cerebellum.forw_N_IO_minus,
        total_time_vect,
        to_file=True,
        label="forw_io-",
    )
]
forw_PC_plus = [
    PopView(
        cerebellum.forw_N_PC,
        total_time_vect,
        to_file=True,
        label="forw_pc+",
    )
]
forw_PC_minus = [
    PopView(
        cerebellum.forw_N_PC_minus,
        total_time_vect,
        to_file=True,
        label="forw_pc-",
    )
]
forw_Glom = [
    PopView(
        cerebellum.forw_N_Glom,
        total_time_vect,
        to_file=True,
        label="forw_glom",
    )
]
forw_GrC = [
    PopView(
        cerebellum.forw_N_GrC,
        total_time_vect,
        to_file=True,
        label="forw_grc",
    )
]
forw_GoC = [
    PopView(
        cerebellum.forw_N_GoC,
        total_time_vect,
        to_file=True,
        label="forw_goc",
    )
]
forw_BC = [
    PopView(
        cerebellum.forw_N_BC,
        total_time_vect,
        to_file=True,
        label="forw_bc",
    )
]
forw_SC = [
    PopView(
        cerebellum.forw_N_SC,
        total_time_vect,
        to_file=True,
        label="forw_sc",
    )
]

inv_Nest_Mf_plus = [
    PopView(
        cerebellum.inv_Nest_Mf[-N_mossy_inv:],
        total_time_vect,
        to_file=True,
        label="inv_mf_plus",
    )
]
inv_Nest_Mf_minus = [
    PopView(
        cerebellum.inv_Nest_Mf[0:N_mossy_inv],
        total_time_vect,
        to_file=True,
        label="inv_mf_minus",
    )
]
inv_DCNp_plus = [
    PopView(
        cerebellum.inv_N_DCNp_plus,
        total_time_vect,
        to_file=True,
        label="inv_dcnp+",
    )
]
inv_DCNp_minus = [
    PopView(
        cerebellum.inv_N_DCNp_minus,
        total_time_vect,
        to_file=True,
        label="inv_dcnp-",
    )
]
inv_IO_plus = [
    PopView(
        cerebellum.inv_N_IO_plus,
        total_time_vect,
        to_file=True,
        label="inv_io+",
    )
]
inv_IO_minus = [
    PopView(
        cerebellum.inv_N_IO_minus,
        total_time_vect,
        to_file=True,
        label="inv_io-",
    )
]
inv_PC_plus = [
    PopView(
        cerebellum.inv_N_PC,
        total_time_vect,
        to_file=True,
        label="inv_pc+",
    )
]
inv_PC_minus = [
    PopView(
        cerebellum.inv_N_PC_minus,
        total_time_vect,
        to_file=True,
        label="inv_pc-",
    )
]
inv_Glom = [
    PopView(
        cerebellum.inv_N_Glom,
        total_time_vect,
        to_file=True,
        label="inv_glom",
    )
]
inv_GrC = [
    PopView(
        cerebellum.inv_N_GrC,
        total_time_vect,
        to_file=True,
        label="inv_grc",
    )
]
inv_GoC = [
    PopView(
        cerebellum.inv_N_GoC,
        total_time_vect,
        to_file=True,
        label="inv_goc",
    )
]
inv_BC = [
    PopView(
        cerebellum.inv_N_BC,
        total_time_vect,
        to_file=True,
        label="inv_bc",
    )
]
inv_SC = [
    PopView(
        cerebellum.inv_N_SC,
        total_time_vect,
        to_file=True,
        label="inv_sc",
    )
]


#### Planner
print("init planner")

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

mc = MotorCortex(N, njt, total_time_vect, motorCommands, **mc_params)
#### State Estimator
print("init state")
kpred = state_se_params["kpred"]
ksens = state_se_params["ksens"]

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
stEst = StateEstimator_mass(N, njt, total_time_vect, **state_params)

# stEst = StateEstimator_mass(N, time_vect, dynSys, state_params)
# %% SPINAL CORD ########################

delay_fbk = params["modules"]["spine"]["fbk_delay"]
wgt_sensNeur_spine = params["modules"]["spine"]["wgt_sensNeur_spine"]

#### Sensory feedback (Parrot neurons on Sensory neurons)
sn_p = []
sn_n = []

for j in range(njt):
    # Positive neurons
    sn_p.append(
        PopView(
            nest.Create("parrot_neuron", N),
            total_time_vect,
            to_file=True,
            label="sn_p",
        )
    )
    # Negative neurons
    sn_n.append(
        PopView(
            nest.Create("parrot_neuron", N),
            total_time_vect,
            to_file=True,
            label="sn_n",
        )
    )

# %% State estimator #######
# Scale the cerebellar prediction up to 1000 Hz
# in order to have firing rate suitable for the State estimator
# and all the other structures inside the control system

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
prediction_p = [PopView(tmp_p, total_time_vect, to_file=True, label="pred_p")]
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
prediction_n = [PopView(tmp_n, total_time_vect, to_file=True, label="pred_n")]

nest.Connect(
    forw_DCNp_plus[0].pop,
    prediction_p[cereb_controlled_joint].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["dcn_forw_prediction"]["weight"],
        "delay": conn_params["dcn_forw_prediction"]["delay"],
    },
)
nest.Connect(
    forw_DCNp_minus[0].pop,
    prediction_p[cereb_controlled_joint].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["dcn_forw_prediction"]["weight"],
        "delay": conn_params["dcn_forw_prediction"]["delay"],
    },
)
nest.Connect(
    forw_DCNp_minus[0].pop,
    prediction_n[cereb_controlled_joint].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["dcn_forw_prediction"]["weight"],
        "delay": conn_params["dcn_forw_prediction"]["delay"],
    },
)
nest.Connect(
    forw_DCNp_plus[0].pop,
    prediction_n[cereb_controlled_joint].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["dcn_forw_prediction"]["weight"],
        "delay": conn_params["dcn_forw_prediction"]["delay"],
    },
)

wgt_fbk_sm_state = params["connections"]["fbk_smoothed_state"]["weight"]
for j in range(njt):
    if j == cereb_controlled_joint:
        # Modify variability sensory feedback ("smoothed")
        fbk_smoothed_p = sn_p[j].pop
        fbk_smoothed_n = sn_n[j].pop

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

# Scale the feedback signal to 0-60 Hz in order to be suitable for the cerebellum
tmp_p = nest.Create("basic_neuron_nestml", N)
nest.SetStatus(
    tmp_p,
    {
        "kp": pops_params["feedback"]["kp"],
        "pos": True,
        "buffer_size": pops_params["feedback"]["buffer_size"],
        "base_rate": pops_params["feedback"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
feedback_p = [PopView(tmp_p, total_time_vect, to_file=True, label="feedback_p")]

tmp_n = nest.Create("basic_neuron_nestml", N)
nest.SetStatus(
    tmp_n,
    {
        "kp": pops_params["feedback"]["kp"],
        "pos": False,
        "buffer_size": pops_params["feedback"]["buffer_size"],
        "base_rate": pops_params["feedback"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
feedback_n = [PopView(tmp_n, total_time_vect, to_file=True, label="feedback_n")]

## modulators for cerebellum
# Motor commands relay neurons
tmp_p = nest.Create("basic_neuron_nestml", N_mossy_forw)
nest.SetStatus(
    tmp_p,
    {
        "kp": pops_params["motor_commands"]["kp"],
        "pos": True,
        "buffer_size": pops_params["motor_commands"]["buffer_size"],
        "base_rate": pops_params["motor_commands"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
motor_commands_p = [
    PopView(tmp_p, total_time_vect, to_file=True, label="motor_commands_p")
]

tmp_n = nest.Create("basic_neuron_nestml", N_mossy_forw)
nest.SetStatus(
    tmp_n,
    {
        "kp": pops_params["motor_commands"]["kp"],
        "pos": False,
        "buffer_size": pops_params["motor_commands"]["buffer_size"],
        "base_rate": pops_params["motor_commands"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
motor_commands_n = [
    PopView(tmp_n, total_time_vect, to_file=True, label="motor_commands_n")
]

# Error signal toward IO neurons ############

# Positive subpopulation
error_p = []
tmp_p = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_p,
    {
        "kp": pops_params["error"]["kp"],
        "pos": True,
        "buffer_size": pops_params["error"]["buffer_size"],
        "base_rate": pops_params["error"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
error_p.append(PopView(tmp_p, total_time_vect, to_file=True, label="error_p"))

# Negative subpopulation
error_n = []
tmp_n = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_n,
    {
        "kp": pops_params["error"]["kp"],
        "pos": False,
        "buffer_size": pops_params["error"]["buffer_size"],
        "base_rate": pops_params["error"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
error_n.append(PopView(tmp_n, total_time_vect, to_file=True, label="error_n"))

# Input to inverse neurons
plan_to_inv_p = []
tmp_p = nest.Create("basic_neuron_nestml", N_mossy_inv)
nest.SetStatus(
    tmp_p,
    {
        "kp": pops_params["plan_to_inv"]["kp"],
        "pos": True,
        "buffer_size": pops_params["plan_to_inv"]["buffer_size"],
        "base_rate": pops_params["plan_to_inv"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
plan_to_inv_p.append(
    PopView(tmp_p, total_time_vect, to_file=True, label="plan_to_inv_p")
)

plan_to_inv_n = []
tmp_n = nest.Create("basic_neuron_nestml", N_mossy_inv)
nest.SetStatus(
    tmp_n,
    {
        "kp": pops_params["plan_to_inv"]["kp"],
        "pos": False,
        "buffer_size": pops_params["plan_to_inv"]["buffer_size"],
        "base_rate": pops_params["plan_to_inv"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
plan_to_inv_n.append(
    PopView(tmp_n, total_time_vect, to_file=True, label="plan_to_inv_n")
)

state_to_inv_p = []
tmp_p = nest.Create("basic_neuron_nestml", N_mossy_inv)
nest.SetStatus(
    tmp_p,
    {
        "kp": pops_params["plan_to_inv"]["kp"],
        "pos": True,
        "buffer_size": pops_params["plan_to_inv"]["buffer_size"],
        "base_rate": pops_params["plan_to_inv"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
state_to_inv_p.append(
    PopView(tmp_p, total_time_vect, to_file=True, label="state_to_inv_p")
)

state_to_inv_n = []
tmp_n = nest.Create("basic_neuron_nestml", N_mossy_inv)
nest.SetStatus(
    tmp_n,
    {
        "kp": pops_params["plan_to_inv"]["kp"],
        "pos": False,
        "buffer_size": pops_params["plan_to_inv"]["buffer_size"],
        "base_rate": pops_params["plan_to_inv"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
state_to_inv_n.append(
    PopView(tmp_n, total_time_vect, to_file=True, label="state_to_inv_n")
)


nest.Connect(
    stEst.pops_p[cereb_controlled_joint].pop,
    state_to_inv_p[0].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["planner_plan_to_inv"]["weight"],
        "delay": conn_params["planner_plan_to_inv"]["delay"],
    },
)
nest.Connect(
    stEst.pops_n[cereb_controlled_joint].pop,
    state_to_inv_n[0].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["planner_plan_to_inv"]["weight"],
        "delay": conn_params["planner_plan_to_inv"]["delay"],
    },
)


motor_prediction_p = []
tmp_p = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_p,
    {
        "kp": pops_params["motor_pred"]["kp"],
        "pos": True,
        "buffer_size": pops_params["motor_pred"]["buffer_size"],
        "base_rate": pops_params["motor_pred"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
motor_prediction_p.append(
    PopView(tmp_p, total_time_vect, to_file=True, label="motor_prediction_p")
)

motor_prediction_n = []
tmp_n = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_n,
    {
        "kp": pops_params["motor_pred"]["kp"],
        "pos": False,
        "buffer_size": pops_params["motor_pred"]["buffer_size"],
        "base_rate": pops_params["motor_pred"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
motor_prediction_n.append(
    PopView(tmp_n, total_time_vect, to_file=True, label="motor_prediction_n")
)

# feedback from sensory
feedback_inv_p = []
tmp_p = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_p,
    {
        "kp": pops_params["feedback_inv"]["kp"],
        "pos": True,
        "buffer_size": pops_params["feedback_inv"]["buffer_size"],
        "base_rate": pops_params["feedback_inv"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
feedback_inv_p.append(
    PopView(tmp_p, total_time_vect, to_file=True, label="feedback_inv_p")
)

feedback_inv_n = []
tmp_n = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_n,
    {
        "kp": pops_params["feedback_inv"]["kp"],
        "pos": False,
        "buffer_size": pops_params["feedback_inv"]["buffer_size"],
        "base_rate": pops_params["feedback_inv"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
feedback_inv_n.append(
    PopView(tmp_n, total_time_vect, to_file=True, label="feedback_inv_n")
)

error_inv_p = []
tmp_p = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_p,
    {
        "kp": pops_params["error_i"]["kp"],
        "pos": True,
        "buffer_size": pops_params["error_i"]["buffer_size"],
        "base_rate": pops_params["error_i"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
error_inv_p.append(PopView(tmp_p, total_time_vect, to_file=True, label="error_inv_p"))

# Negative subpopulation
error_inv_n = []
tmp_n = nest.Create("diff_neuron_nestml", N)
nest.SetStatus(
    tmp_n,
    {
        "kp": pops_params["error_i"]["kp"],
        "pos": False,
        "buffer_size": pops_params["error_i"]["buffer_size"],
        "base_rate": pops_params["error_i"]["base_rate"],
        "simulation_steps": len(total_time_vect),
    },
)
error_inv_n.append(PopView(tmp_n, total_time_vect, to_file=True, label="error_inv_n"))

# %% CONNECTIONS
syn_exc = {"weight": 0.1}  # Synaptic weight of the excitatory synapse
syn_inh = {"weight": -0.1}  # Synaptic weight of the inhibitory synapse

""
# Construct the error signal for both positive and negative neurons
nest.Connect(
    feedback_p[0].pop,
    error_p[0].pop,
    "all_to_all",
    syn_spec={"weight": conn_params["feedback_error"]["weight"]},
)
nest.Connect(
    feedback_p[0].pop,
    error_n[0].pop,
    "all_to_all",
    syn_spec={"weight": conn_params["feedback_error"]["weight"]},
)
nest.Connect(
    feedback_n[0].pop,
    error_p[0].pop,
    "all_to_all",
    syn_spec={"weight": -conn_params["feedback_error"]["weight"]},
)
nest.Connect(
    feedback_n[0].pop,
    error_n[0].pop,
    "all_to_all",
    syn_spec={"weight": -conn_params["feedback_error"]["weight"]},
)

nest.Connect(
    forw_DCNp_plus[0].pop,
    error_p[0].pop,
    {"rule": "all_to_all"},
    syn_spec={"weight": -conn_params["dcn_f_error"]["weight"]},
)
nest.Connect(
    forw_DCNp_plus[0].pop,
    error_n[0].pop,
    {"rule": "all_to_all"},
    syn_spec={"weight": -conn_params["dcn_f_error"]["weight"]},
)
nest.Connect(
    forw_DCNp_minus[0].pop,
    error_p[0].pop,
    {"rule": "all_to_all"},
    syn_spec={"weight": conn_params["dcn_f_error"]["weight"]},
)
nest.Connect(
    forw_DCNp_minus[0].pop,
    error_n[0].pop,
    {"rule": "all_to_all"},
    syn_spec={"weight": conn_params["dcn_f_error"]["weight"]},
)


# Connect error neurons toward IO neurons
nest.Connect(
    error_p[0].pop,
    forw_IO_plus[0].pop,
    {"rule": "all_to_all"},
    conn_params["error_io_f"],
)
# nest.Connect(error_n[0].pop, forw_IO_minus[0].pop,{'rule': 'all_to_all'}, conn_params["error_io_f"])
nest.Connect(
    error_n[0].pop,
    forw_IO_minus[0].pop,
    {"rule": "all_to_all"},
    syn_spec={"weight": -conn_params["error_io_f"]["weight"], "receptor_type": 1},
)


nest.Connect(
    planner.pops_p[cereb_controlled_joint].pop,
    plan_to_inv_p[0].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["planner_plan_to_inv"]["weight"],
        "delay": conn_params["planner_plan_to_inv"]["delay"],
    },
)
nest.Connect(
    planner.pops_n[cereb_controlled_joint].pop,
    plan_to_inv_n[0].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["planner_plan_to_inv"]["weight"],
        "delay": conn_params["planner_plan_to_inv"]["delay"],
    },
)


nest.Connect(plan_to_inv_p[0].pop, inv_Nest_Mf_plus[0].pop, {"rule": "one_to_one"})
nest.Connect(plan_to_inv_n[0].pop, inv_Nest_Mf_minus[0].pop, {"rule": "one_to_one"})
""

""
nest.Connect(
    mc.out_p[cereb_controlled_joint].pop,
    motor_commands_p[0].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["mc_out_motor_commands"]["weight"],
        "delay": conn_params["mc_out_motor_commands"]["delay"],
    },
)
nest.Connect(
    mc.out_n[cereb_controlled_joint].pop,
    motor_commands_n[0].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["mc_out_motor_commands"]["weight"],
        "delay": conn_params["mc_out_motor_commands"]["delay"],
    },
)

nest.Connect(motor_commands_p[0].pop, forw_Nest_Mf_plus[0].pop, {"rule": "one_to_one"})
nest.Connect(motor_commands_n[0].pop, forw_Nest_Mf_minus[0].pop, {"rule": "one_to_one"})

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


nest.Connect(
    sn_p[cereb_controlled_joint].pop,
    feedback_p[0].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["sn_fbk_smoothed"]["weight"],
        "delay": conn_params["sn_fbk_smoothed"]["delay"],
    },
)
nest.Connect(
    sn_n[cereb_controlled_joint].pop,
    feedback_n[0].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["sn_fbk_smoothed"]["weight"],
        "delay": conn_params["sn_fbk_smoothed"]["delay"],
    },
)

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


nest.Connect(
    inv_DCNp_minus[0].pop,
    motor_prediction_p[0].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["dcn_i_motor_pred"]["weight"],
        "delay": conn_params["dcn_i_motor_pred"]["delay"],
    },
)
nest.Connect(
    inv_DCNp_plus[0].pop,
    motor_prediction_p[0].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["dcn_i_motor_pred"]["weight"],
        "delay": conn_params["dcn_i_motor_pred"]["delay"],
    },
)
nest.Connect(
    inv_DCNp_minus[0].pop,
    motor_prediction_n[0].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["dcn_i_motor_pred"]["weight"],
        "delay": conn_params["dcn_i_motor_pred"]["delay"],
    },
)
nest.Connect(
    inv_DCNp_plus[0].pop,
    motor_prediction_n[0].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["dcn_i_motor_pred"]["weight"],
        "delay": conn_params["dcn_i_motor_pred"]["delay"],
    },
)

# Construct the error signal for both positive and negative neurons
nest.Connect(
    plan_to_inv_p[0].pop,
    error_inv_p[0].pop,
    {"rule": "all_to_all"},
    syn_spec={
        "weight": conn_params["plan_to_inv_error_inv"]["weight"],
        "delay": conn_params["plan_to_inv_error_inv"]["delay"],
    },
)
nest.Connect(
    plan_to_inv_n[0].pop,
    error_inv_p[0].pop,
    {"rule": "all_to_all"},
    syn_spec={
        "weight": -conn_params["plan_to_inv_error_inv"]["weight"],
        "delay": conn_params["plan_to_inv_error_inv"]["delay"],
    },
)
nest.Connect(
    plan_to_inv_p[0].pop,
    error_inv_n[0].pop,
    {"rule": "all_to_all"},
    syn_spec={
        "weight": conn_params["plan_to_inv_error_inv"]["weight"],
        "delay": conn_params["plan_to_inv_error_inv"]["delay"],
    },
)
nest.Connect(
    plan_to_inv_n[0].pop,
    error_inv_n[0].pop,
    {"rule": "all_to_all"},
    syn_spec={
        "weight": -conn_params["plan_to_inv_error_inv"]["weight"],
        "delay": conn_params["plan_to_inv_error_inv"]["delay"],
    },
)

nest.Connect(
    error_inv_p[0].pop,
    inv_IO_plus[0].pop,
    {"rule": "all_to_all"},
    conn_params["error_inv_io_i"],
)
nest.Connect(
    error_inv_n[0].pop,
    inv_IO_minus[0].pop,
    {"rule": "all_to_all"},
    conn_params["error_inv_io_i"],
)
""

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
        PopView(tmp_p, time_vect, to_file=True, label="brainstem_p")
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
        PopView(tmp_n, time_vect, to_file=True, label="brainstem_n")
    )


nest.Connect(
    motor_prediction_p[0].pop,
    brain_stem_new_p[cereb_controlled_joint].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["motor_pre_brain_stem"]["weight"],
        "delay": conn_params["motor_pre_brain_stem"]["delay"],
    },
)
nest.Connect(
    motor_prediction_n[0].pop,
    brain_stem_new_n[cereb_controlled_joint].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["motor_pre_brain_stem"]["weight"],
        "delay": conn_params["motor_pre_brain_stem"]["delay"],
    },
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


nest.Connect(
    sn_p[cereb_controlled_joint].pop,
    feedback_inv_p[0].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["sn_feedback_inv"]["weight"],
        "delay": conn_params["sn_feedback_inv"]["delay"],
    },
)
nest.Connect(
    sn_n[cereb_controlled_joint].pop,
    feedback_inv_n[0].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["sn_feedback_inv"]["weight"],
        "delay": conn_params["sn_feedback_inv"]["delay"],
    },
)

"""
nest.Connect(stEst.pops_p[j].pop, error_inv_p[0].pop, "all_to_all", syn_spec={"weight": conn_params["state_error_inv"]["weight"], "delay": conn_params["state_error_inv"]["delay"]})
nest.Connect(stEst.pops_p[j].pop, error_inv_n[0].pop, "all_to_all", syn_spec={"weight": conn_params["state_error_inv"]["weight"], "delay": conn_params["state_error_inv"]["delay"]})
nest.Connect(stEst.pops_n[j].pop, error_inv_n[0].pop, "all_to_all", syn_spec={"weight": -conn_params["state_error_inv"]["weight"], "delay": conn_params["state_error_inv"]["delay"]})
nest.Connect(stEst.pops_n[j].pop, error_inv_p[0].pop, "all_to_all", syn_spec={"weight": -conn_params["state_error_inv"]["weight"], "delay": conn_params["state_error_inv"]["delay"]})
"""
nest.Connect(
    state_to_inv_p[j].pop,
    error_inv_p[0].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["plan_to_inv_error_inv"]["weight"],
        "delay": conn_params["plan_to_inv_error_inv"]["delay"],
    },
)
nest.Connect(
    state_to_inv_p[j].pop,
    error_inv_n[0].pop,
    "all_to_all",
    syn_spec={
        "weight": conn_params["plan_to_inv_error_inv"]["weight"],
        "delay": conn_params["plan_to_inv_error_inv"]["delay"],
    },
)
nest.Connect(
    state_to_inv_n[j].pop,
    error_inv_n[0].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["plan_to_inv_error_inv"]["weight"],
        "delay": conn_params["plan_to_inv_error_inv"]["delay"],
    },
)
nest.Connect(
    state_to_inv_p[j].pop,
    error_inv_p[0].pop,
    "all_to_all",
    syn_spec={
        "weight": -conn_params["plan_to_inv_error_inv"]["weight"],
        "delay": conn_params["plan_to_inv_error_inv"]["delay"],
    },
)

# %% MUSIC CONFIG

msc = MusicCfg()

#### MUSIC output port (with nTot channels)
proxy_out = nest.Create("music_event_out_proxy", 1, params={"port_name": "mot_cmd_out"})

# ii=0
# for j in range(njt):
#     for i, n in enumerate(mc.out_p[j].pop):
#         nest.Connect([n], proxy_out, "one_to_one",{'music_channel': ii})
#         ii=ii+1
#     for i, n in enumerate(mc.out_n[j].pop):
#         nest.Connect([n], proxy_out, "one_to_one",{'music_channel': ii})
#         ii=ii+1

# ii=0
# # for j in range(njt):
# for i, n in enumerate(brain_stem_p):
#     nest.Connect([n], proxy_out, "one_to_one",{'music_channel': ii})
#     ii=ii+1
# for i, n in enumerate(mc.out_p[1].pop):
#     nest.Connect([n], proxy_out, "one_to_one",{'music_channel': ii})
#     ii=ii+1
# for i, n in enumerate(brain_stem_n):
#     nest.Connect([n], proxy_out, "one_to_one",{'music_channel': ii})
#     ii=ii+1
# for i, n in enumerate(mc.out_n[1].pop):
#     nest.Connect([n], proxy_out, "one_to_one",{'music_channel': ii})
#     ii=ii+1


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
"""
spikedetector_fbk_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback pos"})
spikedetector_fbk_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback neg"})

spikedetector_fbk_inv_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback inv pos"})
spikedetector_fbk_inv_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback inv neg"})

spikedetector_fbk_cereb_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback cerebellum pos"})
spikedetector_fbk_cereb_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback cerebellum neg"})
spikedetector_io_forw_input_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Input inferior Olive Forw pos"})
spikedetector_io_forw_input_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Input inferior Olive Forw neg"})

spikedetector_io_inv_input_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Input inferior Olive Inv pos"})
spikedetector_io_inv_input_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Input inferior Olive Inv neg"})

spikedetector_stEst_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "State estimator pos"})
spikedetector_stEst_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "State estimator neg"})
spikedetector_planner_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Planner pos"})
spikedetector_planner_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Planner neg"})
spikedetector_pred_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Cereb pred pos"})
spikedetector_pred_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Cereb pred neg"})
spikedetector_motor_pred_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Cereb motor pred pos"})
spikedetector_motor_pred_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Cereb motor pred neg"})
spikedetector_stEst_max_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "State estimator Max pos"})
spikedetector_stEst_max_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "State estimator Max neg"})
spikedetector_fbk_smoothed_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback smoothed pos"})
spikedetector_fbk_smoothed_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Feedback smoothed neg"})

spikedetector_motor_comm_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Motor Command pos"})
spikedetector_motor_comm_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Motor Command neg"})

spikedetector_plan_to_inv_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Plan to inv pos"})
spikedetector_plan_to_inv_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Plan to inv neg"})

spikedetector_brain_stem_pos = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Brain stem pos"})
spikedetector_brain_stem_neg = nest.Create("spike_detector", params={"withgid": True,"withtime": True, "to_file": True, "label": "Brain stem neg"})

nest.Connect(motor_commands_p, spikedetector_motor_comm_pos)
nest.Connect(motor_commands_n, spikedetector_motor_comm_neg)

nest.Connect(brain_stem_new_p[cereb_controlled_joint].pop, spikedetector_brain_stem_pos)
nest.Connect(brain_stem_new_n[cereb_controlled_joint].pop, spikedetector_brain_stem_neg)

nest.Connect(plan_to_inv_p, spikedetector_plan_to_inv_pos)
nest.Connect(plan_to_inv_n, spikedetector_plan_to_inv_neg)

nest.Connect(sn_p[cereb_controlled_joint].pop, spikedetector_fbk_pos)
nest.Connect(sn_n[cereb_controlled_joint].pop, spikedetector_fbk_neg)
nest.Connect(feedback_p, spikedetector_fbk_cereb_pos)
nest.Connect(feedback_n, spikedetector_fbk_cereb_neg)

nest.Connect(feedback_inv_p, spikedetector_fbk_inv_pos)
nest.Connect(feedback_inv_n, spikedetector_fbk_inv_pos)
''
nest.Connect(error_p, spikedetector_io_forw_input_pos)
nest.Connect(error_n, spikedetector_io_forw_input_neg)

nest.Connect(error_inv_p, spikedetector_io_inv_input_pos)
nest.Connect(error_inv_n, spikedetector_io_inv_input_neg)
# ''
# nest.Connect(se.out_p[cereb_controlled_joint].pop, spikedetector_stEst_pos)
# nest.Connect(se.out_n[cereb_controlled_joint].pop, spikedetector_stEst_neg)

nest.Connect(planner.pops_p[cereb_controlled_joint].pop, spikedetector_planner_pos)
nest.Connect(planner.pops_n[cereb_controlled_joint].pop, spikedetector_planner_neg)
''
nest.Connect(prediction_p, spikedetector_pred_pos)
nest.Connect(prediction_n, spikedetector_pred_neg)

nest.Connect(motor_prediction_p, spikedetector_motor_pred_pos)
nest.Connect(motor_prediction_n, spikedetector_motor_pred_neg)
''
nest.Connect(stEst.pops_p[cereb_controlled_joint].pop, spikedetector_stEst_max_pos)
nest.Connect(stEst.pops_n[cereb_controlled_joint].pop, spikedetector_stEst_max_neg)
''
nest.Connect(fbk_smoothed_p, spikedetector_fbk_smoothed_pos)
nest.Connect(fbk_smoothed_n, spikedetector_fbk_smoothed_neg)
''

##### Weight recorder created manually #####
parallel_fiber_to_basket = cerebellum.forward_model.get_connectivity_set("parallel_fiber_to_basket")
pf_bc = np.unique(parallel_fiber_to_basket.from_identifiers)[0:5000]
basket = np.unique(parallel_fiber_to_basket.to_identifiers)
bc_nest = cerebellum.tuning_adapter.get_nest_ids(basket)
bc_pos = np.intersect1d(bc_nest, cerebellum.Nest_ids['basket_cell']['positive'])
bc_neg = np.intersect1d(bc_nest, cerebellum.Nest_ids['basket_cell']['negative'])
pf_to_basket_pos = nest.GetConnections(source = cerebellum.tuning_adapter.get_nest_ids(pf_bc), target = list(bc_pos))
print('Number of pf-BC pos: ', len(pf_to_basket_pos))
pf_to_basket_neg = nest.GetConnections(source = cerebellum.tuning_adapter.get_nest_ids(pf_bc), target = list(bc_neg))
print('Number of pf-BC neg: ', len(pf_to_basket_neg))
Nest_pf_to_basket = (pf_to_basket_pos + pf_to_basket_neg)

parallel_fiber_to_stellate = cerebellum.scaffold_model.get_connectivity_set("parallel_fiber_to_stellate")
pf_sc = np.unique(parallel_fiber_to_stellate.from_identifiers)[0:5000]
stellate = np.unique(parallel_fiber_to_stellate.to_identifiers)
sc_nest = cerebellum.tuning_adapter.get_nest_ids(stellate)
sc_pos = np.intersect1d(sc_nest, cerebellum.Nest_ids['stellate_cell']['positive'])
sc_neg = np.intersect1d(sc_nest, cerebellum.Nest_ids['stellate_cell']['negative'])
pf_to_stellate_pos = nest.GetConnections(source = cerebellum.tuning_adapter.get_nest_ids(pf_sc), target = list(sc_pos))
print('Number of pf-SC pos: ', len(pf_to_stellate_pos))
pf_to_stellate_neg = nest.GetConnections(source = cerebellum.tuning_adapter.get_nest_ids(pf_sc), target = list(sc_neg))
print('Number of pf-SC neg: ', len(pf_to_stellate_neg))
Nest_pf_to_stellate = (pf_to_stellate_pos + pf_to_stellate_neg)

parallel_fiber_to_purkinje = cerebellum.scaffold_model.get_connectivity_set("parallel_fiber_to_purkinje")
pf_pc = np.unique(parallel_fiber_to_purkinje.from_identifiers)[0:10000]
purkinje = np.unique(parallel_fiber_to_purkinje.to_identifiers)
pc_nest = cerebellum.tuning_adapter.get_nest_ids(purkinje)
pc_pos = np.intersect1d(pc_nest, cerebellum.Nest_ids['purkinje_cell']['positive'])
pc_neg = np.intersect1d(pc_nest, cerebellum.Nest_ids['purkinje_cell']['negative'])
pf_to_purkinje_pos = nest.GetConnections(source = cerebellum.tuning_adapter.get_nest_ids(pf_pc), target = list(pc_pos))
print('Number of pf-PC pos: ', len(pf_to_purkinje_pos))
pf_to_purkinje_neg = nest.GetConnections(source = cerebellum.tuning_adapter.get_nest_ids(pf_pc), target = list(pc_neg))
print('Number of pf-PC neg: ', len(pf_to_purkinje_neg))
Nest_pf_to_purkinje = (pf_to_purkinje_pos + pf_to_purkinje_neg)

weights = np.array(nest.GetStatus(Nest_pf_to_basket, "weight"))
if mpi4py.MPI.COMM_WORLD.rank == 0:
    print('Number of pf-BC connections: ',weights.shape[0])
    weights_pf_bc = np.empty((weights.shape[0], n_trial+1))
    weights_pf_bc[:,0] = weights

weights = np.array(nest.GetStatus(Nest_pf_to_stellate, "weight"))
if mpi4py.MPI.COMM_WORLD.rank == 0:
    print('Number of pf-SC connections: ',weights.shape[0])
    weights_pf_sc = np.empty((weights.shape[0], n_trial+1))
    weights_pf_sc[:,0] = weights

weights = np.array(nest.GetStatus(Nest_pf_to_purkinje, "weight"))
if mpi4py.MPI.COMM_WORLD.rank == 0:
    print('Number of pf-PC connections: ',weights.shape[0])
    weights_pf_pc = np.empty((weights.shape[0], n_trial+1))
    weights_pf_pc[:,0] = weights
"""

###################### SIMULATE ######################
# nest.SetKernelStatus({"data_path": pathDat})
total_len = int(time_span)
"""
# Disable Sensory feedback in State estimation (TODO togliere)
conns_pos = nest.GetConnections(source = fbk_smoothed_p, target = stEst.pops_p[cereb_controlled_joint].pop)
conns_neg = nest.GetConnections(source = fbk_smoothed_n, target = stEst.pops_n[cereb_controlled_joint].pop)
nest.SetStatus(conns_pos, {"weight": 0.0})
nest.SetStatus(conns_neg, {"weight": 0.0})

# Disable Cerebellar prediction in State estimation for the first 5 trials
''
conns_pos_forw = nest.GetConnections(source = prediction_p[cereb_controlled_joint].pop, target = stEst.pops_p[cereb_controlled_joint].pop)
conns_neg_forw = nest.GetConnections(source = prediction_n[cereb_controlled_joint].pop, target = stEst.pops_n[cereb_controlled_joint].pop)
''
conns_pos_inv = nest.GetConnections(source = motor_prediction_p, target = brain_stem_new_p[cereb_controlled_joint].pop)
conns_neg_inv = nest.GetConnections(source = motor_prediction_n, target = brain_stem_new_n[cereb_controlled_joint].pop)
''
# I can't disconnect cereb-State if the Prediction_error = state - cereb
# I can disconnect the cerebellum only if the error = Feedback - cereb
''
if cerebellum_application_inv != 0:
    nest.SetStatus(conns_pos_inv, {"weight": 0.0})
    nest.SetStatus(conns_neg_inv, {"weight": 0.0})
''
if cerebellum_application_forw != 0:
    nest.SetStatus(conns_pos_forw, {"weight": 0.0})
    nest.SetStatus(conns_neg_forw, {"weight": 0.0})
"""
# nest.SetKernelStatus({"data_path": pthDat})
total_len = int(time_span)
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
    forw_Nest_Mf_plus,
    forw_Nest_Mf_minus,
    forw_DCNp_plus,
    forw_DCNp_minus,
    forw_IO_plus,
    forw_IO_minus,
    inv_Nest_Mf_plus,
    inv_Nest_Mf_minus,
    inv_DCNp_plus,
    inv_DCNp_minus,
    inv_IO_plus,
    inv_IO_minus,
    feedback_p,
    feedback_n,
    motor_commands_p,
    motor_commands_n,
    error_p,
    error_n,
    plan_to_inv_p,
    plan_to_inv_n,
    motor_prediction_p,
    motor_prediction_n,
    feedback_inv_p,
    feedback_inv_n,
    error_inv_p,
    error_inv_n,
    forw_PC_plus,
    forw_PC_minus,
    inv_PC_plus,
    inv_PC_minus,
    state_to_inv_p,
    state_to_inv_n,
]

time_network = timedelta(seconds=timer() - start)
for trial in range(n_trials):
    print("rank: ", mpi4py.MPI.COMM_WORLD.rank)
    if mpi4py.MPI.COMM_WORLD.rank == 0:
        print("Simulating trial {} lasting {} ms".format(trial + 1, total_len))
    """
    if trial == cerebellum_application_inv:
        nest.SetStatus(conns_pos_inv, {"weight": -conn_params["motor_pre_brain_stem"]["weight"]})
        nest.SetStatus(conns_neg_inv, {"weight": conn_params["motor_pre_brain_stem"]["weight"]})
    if trial == cerebellum_application_forw:
        nest.SetStatus(conns_pos_forw, {"weight": conn_params["pred_state"]["weight"]})
        nest.SetStatus(conns_neg_forw, {"weight": -conn_params["pred_state"]["weight"]})
    """
    print("sto per simulare")
    nest.Simulate(total_len)
    collapse_files(pathData, names, pops, njt)
    print("finito")
"""
#%% SIMULATE ######################
#nest.SetKernelStatus({"data_path": pthDat})
total_len = int(time_span)
for trial in range(n_trial):
    if mpi4py.MPI.COMM_WORLD.rank == 0:
        print('Simulating trial {} lasting {} ms'.format(trial+1,total_len))
    nest.Simulate(total_len)

"""
# Add weights to weigth_recorder
# Pf-BC
"""
weights = np.array(nest.GetStatus(Nest_pf_to_basket, "weight"))
if mpi4py.MPI.COMM_WORLD.rank == 0:
    weights_pf_bc[:,trial+1] = weights
# Pf_SC
    weights = np.array(nest.GetStatus(Nest_pf_to_stellate, "weight"))
if mpi4py.MPI.COMM_WORLD.rank == 0:
    weights_pf_sc[:,trial+1] = weights
# Pf-PC
    weights = np.array(nest.GetStatus(Nest_pf_to_purkinje, "weight"))
if mpi4py.MPI.COMM_WORLD.rank == 0:
        weights_pf_pc[:,trial+1] = weights
"""

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
        plt.suptitle("Planner", fontsize=20)
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
        plt.suptitle("MC - Ffwd", fontsize=20)
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
    reference_plus = [rate_p, rate_n]
    reference_minus = [rate_stEst_p, rate_stEst_n]
    reference_diff = [rate_p - rate_stEst_p, rate_n - rate_stEst_n]
    time_vecs = [
        bins_p[:-1],
        bins_n[:-1],
        bins_p[:-1],
        bins_n[:-1],
        bins_p[:-1],
        bins_n[:-1],
    ]

    legend = [
        "planner_p",
        "planner_n",
        "state_p",
        "state_n",
        "diff_p",
        "diff_n",
        "diff_p -diff_n",
    ]
    styles = ["r--", "b--", "r--", "b--", "r--", "b--", "k--"]
    for i in range(njt):
        plotPopulation_diff(
            time_vect_paused,
            mc.fbk_p[i],
            mc.fbk_n[i],
            reference_plus,
            reference_minus,
            reference_diff,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("MC - Fbk", fontsize=20)
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
        plt.suptitle("MC - Out", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/mc_out_"+lgd[i]+".png")
            plt.savefig(pathFig + "mc_out_" + lgd[i] + ".png")

    bins_p, count_p, rate_p = mc.out_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = mc.out_n[0].computePSTH(time_vect_paused, 15)
    bins_p_inv, count_p_inv, rate_p_inv = motor_prediction_p[0].computePSTH(
        time_vect_paused, 15
    )
    bins_n_inv, count_n_inv, rate_n_inv = motor_prediction_n[0].computePSTH(
        time_vect_paused, 15
    )

    reference = [rate_p, rate_n, rate_p_inv, rate_n_inv]
    time_vecs = [bins_p[:-1], bins_n[:-1], bins_p_inv[:-1], bins_n_inv[:-1]]
    legend = ["out_p", "out_n", "pred_p", "pred_n"]
    styles = ["r", "b", "r--", "b--"]
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
        plt.suptitle("Brainstem", fontsize=20)
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
        plt.suptitle("Sensory feedback", fontsize=20)
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
        plt.suptitle("State", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "state_" + lgd[i] + ".png")

    # Mossy fibers
    # Forward
    bins_p, count_p, rate_p = motor_commands_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = motor_commands_n[0].computePSTH(time_vect_paused, 15)
    reference = [rate_p, rate_n]
    time_vecs = [bins_p[:-1], bins_n[:-1]]
    legend = ["motor commands_p", "motor_commands_n"]
    styles = ["r--", "b--"]
    print("Forward - mf")

    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            forw_Nest_Mf_plus[i],
            forw_Nest_Mf_minus[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Forward - mf", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "forw_mf_" + lgd[i] + ".png")

    # Inverse
    bins_p, count_p, rate_p = plan_to_inv_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = plan_to_inv_n[0].computePSTH(time_vect_paused, 15)

    reference = [rate_p, rate_n]
    time_vecs = [bins_p[:-1], bins_n[:-1]]
    legend = ["plan_to_inv_p", "plan_to_inv_n"]
    styles = ["r--", "b--"]
    print("Inverse - mf")

    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            inv_Nest_Mf_plus[i],
            inv_Nest_Mf_minus[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Inverse - mf", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "inv_mf_" + lgd[i] + ".png")

    # IO
    # Forward
    bins_p, count_p, rate_p = error_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = error_n[0].computePSTH(time_vect_paused, 15)

    reference = [rate_p, rate_n]
    time_vecs = [bins_p[:-1], bins_n[:-1]]
    legend = ["error_p", "error_n"]
    styles = ["r--", "b--"]
    print("Forward - IO")

    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            forw_IO_plus[i],
            forw_IO_minus[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Forward - IO", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "forw_io_" + lgd[i] + ".png")

    # Inverse
    bins_p, count_p, rate_p = error_inv_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = error_inv_n[0].computePSTH(time_vect_paused, 15)
    reference = [rate_p, rate_n]
    time_vecs = [bins_p[:-1], bins_n[:-1]]
    legend = ["error_inv_p", "error_inv_n"]
    styles = ["r--", "b--"]
    print("Inverse - IO")

    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            inv_IO_plus[i],
            inv_IO_minus[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Inverse - IO", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "inv_io_" + lgd[i] + ".png")

    # DCN (only output -> no reference)
    # Forward
    reference = []
    time_vecs = []
    legend = []
    styles = []
    print("forw DCN")

    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            forw_DCNp_plus[i],
            forw_DCNp_minus[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Forward - DCN", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "forw_DCN" + lgd[i] + ".png")

    # Inverse
    print("inv DCN")
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            inv_DCNp_plus[i],
            inv_DCNp_minus[i],
            reference,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Inverse - DCN", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "inv_DCN" + lgd[i] + ".png")

    # Error signals for IOs
    # Forward
    bins_p, count_p, rate_p = feedback_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = feedback_n[0].computePSTH(time_vect_paused, 15)

    bins_p_DCN, count_p_DCN, rate_p_DCN = forw_DCNp_plus[0].computePSTH(
        time_vect_paused, 15
    )
    bins_n_DCN, count_n_DCN, rate_n_DCN = forw_DCNp_minus[0].computePSTH(
        time_vect_paused, 15
    )

    reference_plus = [rate_p, rate_n]
    reference_minus = [rate_p_DCN, rate_n_DCN]
    reference_diff = [rate_p - rate_p_DCN, rate_n - rate_n_DCN]
    time_vecs = [
        bins_p[:-1],
        bins_n[:-1],
        bins_p[:-1],
        bins_n[:-1],
        bins_p[:-1],
        bins_n[:-1],
    ]
    legend = [
        "feedback_p",
        "feedback_n",
        "DCNp_plus",
        "DCNp_minus",
        "diff_p",
        "diff_n",
        "diff_p - diff_n",
    ]
    styles = ["r--", "b--", "r--", "b--", "r--", "b--", "k--"]
    print("error to forw io")

    for i in range(njt):
        plotPopulation_diff(
            time_vect_paused,
            error_p[i],
            error_n[i],
            reference_plus,
            reference_minus,
            reference_diff,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Forward - prediction error", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "error_to_forw_io_" + lgd[i] + ".png")

    # Inverse
    bins_p, count_p, rate_p = plan_to_inv_p[0].computePSTH(time_vect_paused, 15)
    bins_n, count_n, rate_n = plan_to_inv_n[0].computePSTH(time_vect_paused, 15)

    bins_stEst_p, count_stEst_p, rate_stEst_p = state_to_inv_p[0].computePSTH(
        time_vect_paused, 15
    )
    bins_stEst_n, count_stEst_n, rate_stEst_n = state_to_inv_n[0].computePSTH(
        time_vect_paused, 15
    )

    reference_plus = [rate_p, rate_n]
    reference_minus = [rate_stEst_p, rate_stEst_n]
    reference_diff = [rate_p - rate_stEst_p, rate_n - rate_stEst_n]
    time_vecs = [
        bins_p[:-1],
        bins_n[:-1],
        bins_p[:-1],
        bins_n[:-1],
        bins_p[:-1],
        bins_n[:-1],
    ]
    legend = [
        "plan_to_inv_p",
        "plan_to_inv_n",
        "state_p",
        "state_n",
        "diff_p",
        "diff_n",
        "diff_p - diff_n",
    ]
    styles = ["r--", "b--", "r--", "b--", "r--", "b--", "k--"]
    print("error to inv io")

    for i in range(njt):
        plotPopulation_diff(
            time_vect_paused,
            error_inv_p[i],
            error_inv_n[i],
            reference_plus,
            reference_minus,
            reference_diff,
            time_vecs,
            legend,
            styles,
            title=lgd[i],
            buffer_size=15,
        )
        plt.suptitle("Inverse - prediction error", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/state_"+lgd[i]+".png")
            plt.savefig(pathFig + "error_to_inv_io_" + lgd[i] + ".png")

    reference = []
    time_vecs = []
    legend = []
    styles = []
    print("forw_pc")
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            forw_PC_plus[i],
            forw_PC_minus[i],
            reference,
            time_vecs,
            legend,
            styles,
            buffer_size=15,
        )
        plt.suptitle("Forward -PCs", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/sensory_"+lgd[i]+".png")
            plt.savefig(pathFig + "forw_PC_" + lgd[i] + ".png")

    reference = []
    time_vecs = []
    legend = []
    styles = []
    print("inv_pc")
    for i in range(njt):
        plotPopulation(
            time_vect_paused,
            inv_PC_plus[i],
            inv_PC_minus[i],
            reference,
            time_vecs,
            legend,
            styles,
            buffer_size=15,
        )
        plt.suptitle("Inverse - PCs", fontsize=20)
        if saveFig:
            # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/sensory_"+lgd[i]+".png")
            plt.savefig(pathFig + "inv_PC_" + lgd[i] + ".png")


time_brainpy = timedelta(seconds=timer() - start)

print(
    f"final times:\ncerebellum: {time_cerebellum}\nnetwork: {time_network}\nbrain.py: {time_brainpy}"
)
