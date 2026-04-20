#!/usr/bin/env python3

import json
import queue
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import music
import numpy as np
from arm_1dof.bullet_arm_1dof import BulletArm1Dof
from arm_1dof.robot_arm_1dof import RobotArm1Dof

# from data_handling import add_entry, collapse_files_bullet
from mpi4py import MPI

# Just to get the following imports right!
sys.path.insert(1, "../")


# ctypes.CDLL("libmpi.so", mode=ctypes.RTLD_GLOBAL)
import json
import random
import time

from settings import SEED

import trajectories as tj
from complete_control.settings import Brain, Experiment, MusicCfg, Simulation
from sensoryneuron import SensoryNeuron

from ..paths import RunPaths

# from util import plotPopulation

# import perturbation as pt


setup = music.Setup()

random.seed = SEED
np.random.seed(SEED)
print("attempting broadcast")
shared_data = {
    "timestamp": None,
    "paths": None,
}
run_timestamp_str, run_paths = None, None
shared_data = MPI.COMM_WORLD.bcast(shared_data, root=0)
run_timestamp_str = shared_data["timestamp"]
run_paths: RunPaths = shared_data["paths"]


exp = Experiment()

# param_file = exp.param_file
saveFig = True

# Opening JSON file
f = open("new_params.json")

params = json.load(f)
print(params["modules"])
f.close()

mc_params = params["modules"]["motor_cortex"]
plan_params = params["modules"]["planner"]
spine_params = params["modules"]["spine"]

state_params = params["modules"]["state"]
state_se_params = params["modules"]["state_se"]

pops_params = params["pops"]
conn_params = params["connections"]


# f = open(pathFig+"params.json","w")
# json.dump(params, f, indent =6)
# f.close()

# %%  SIMULATION

###################### SIMULATION ######################

sim = Simulation()

res = sim.resolution / 1e3  # Resolution (translate into seconds)
timeMax = sim.timeMax / 1e3  # Maximum time (translate into seconds)
time = np.arange(0, timeMax + res, res)  # Time vector

time_pause = 0
time_wait = sim.timeWait / 1e3  # Pause time (translate into seconds)
# print('time_wait: ', sim.timeWait)

time_wait_vec = np.arange(0, sim.timeWait, sim.resolution)
steps_wait = len(time_wait_vec)
# print('len(time_wait_vec):' , len(time_wait_vec))
n_trial = sim.n_trials
time_trial = time_wait + timeMax
exp_duration = (timeMax + time_wait) * n_trial
print("exp_duration: ", exp_duration)
time_tot = np.arange(0, exp_duration, res)
print("time_tot: ", time_tot)
n_time = len(time_tot)
print("n_time: ", n_time)
# scale   = -350000.0# mc_params["ffwd_kp"]#   # Scaling coefficient to translate spike rates into forces (must be >=1)
scale = 500000.0
scale_des = scale / scale
bufSize = 10 / 1e3  # Buffer to calculate spike rate (seconds)


######################## INIT BULLET ##########################

# Initialize bullet and load robot
bullet = BulletArm1Dof()
# bullet.InitPybullet()

import pybullet as p

bullet.InitPybullet(bullet_connect=p.GUI)  # , g=[0.0, 0.0 , -9.81])
bullet_robot = bullet.LoadRobot()


upperarm = p.getLinkState(
    bullet_robot._body_id, RobotArm1Dof.UPPER_ARM_LINK_ID, computeLinkVelocity=True
)[0]
forearm = p.getLinkState(
    bullet_robot._body_id, RobotArm1Dof.FOREARM_LINK_ID, computeLinkVelocity=True
)[0]
hand = p.getLinkState(
    bullet_robot._body_id, RobotArm1Dof.HAND_LINK_ID, computeLinkVelocity=True
)[0]

# hand = bullet_robot.EEPose()[0]
# _init_pos = [hand[0], hand[2]]  # NO! only update it after resetting joint state


# rho = np.linalg.norm(np.array(upperarm) - np.array(hand))
# z = upperarm[2] - rho * np.cos(1.57)
# y = upperarm[0] + rho * np.sin(1.57)
# _tgt_pos = [y, z]
# _desired_initial_angle = 45
def compute_absolute_pos_ee(angle, p, bullet_robot):
    upperarm = p.getLinkState(
        bullet_robot._body_id, RobotArm1Dof.UPPER_ARM_LINK_ID, computeLinkVelocity=True
    )[0]
    hand = p.getLinkState(
        bullet_robot._body_id, RobotArm1Dof.HAND_LINK_ID, computeLinkVelocity=True
    )[0]
    rho = np.linalg.norm(np.array(upperarm) - np.array(hand))
    print("according to pybullet, upperarm is at ", upperarm[2], type(upperarm[2]), rho)

    y = upperarm[0] + rho * np.sin(angle)
    z = upperarm[2] - rho * np.cos(angle)
    return (y, z)


##################### EXPERIMENT #####################
# pathFig =exp.pathFig
pathFig = str(run_paths.figures_receiver.absolute()) + "/"
pthDat = str(run_paths.data_bullet.absolute()) + "/"
# pthDat = exp.pathData + "bullet/"
cond = exp.cond

"""
# Perturbation
angle = exp.frcFld_angle
k     = 0                # Default = No Force field
ff_application = exp.ff_application
ff_removal = exp.ff_removal
"""
# Dynamical system
dynSys = exp.dynSys
njt = exp.dynSys.numVariables()

# Desired trajectories (only used for testing)
# End-effector space
init_pos_ee = exp.init_pos_ee
tgt_pos_ee = exp.tgt_pos_ee


init_pos = dynSys.inverseKin(init_pos_ee)
tgt_pos = dynSys.inverseKin(tgt_pos_ee)
# trj, pol = tj.minimumJerk(init_pos[0], tgt_pos[0], time)
trj = np.loadtxt("trajectory.txt")

# Joint space
trj_ee = dynSys.forwardKin(trj)
trj_d = np.gradient(trj, res, axis=0)
trj_dd = np.gradient(trj_d, res, axis=0)
inputDes = exp.dynSys.inverseDyn(trj, trj_d, trj_dd) / scale_des

p.resetJointState(bullet_robot._body_id, RobotArm1Dof.ELBOW_JOINT_ID, 0)
hand_at_zero = p.getLinkState(
    bullet_robot._body_id, RobotArm1Dof.HAND_LINK_ID, computeLinkVelocity=True
)[0]
print(f"hand at zero {hand_at_zero}")


p.resetJointState(
    bullet_robot._body_id, RobotArm1Dof.ELBOW_JOINT_ID, exp._tgt_joint_angle
)
hand_at_desired = p.getLinkState(
    bullet_robot._body_id, RobotArm1Dof.HAND_LINK_ID, computeLinkVelocity=True
)[0]
_desired_abs_tgt_ee = (hand_at_desired[0], hand_at_desired[2])


print(f"\n\n\n _desired_abs_tgt_ee={_desired_abs_tgt_ee}")
############################ BRAIN ############################
p.resetJointState(
    bullet_robot._body_id, RobotArm1Dof.ELBOW_JOINT_ID, exp.init_pos_angle
)
hand_at_effective_start = p.getLinkState(
    bullet_robot._body_id, RobotArm1Dof.HAND_LINK_ID, computeLinkVelocity=True
)[0]

brain = Brain()

# Number of neurons (for each subpopulation positive/negative)
N = brain.nNeurPop

# Weight (motor cortex - motor neurons)
w = spine_params["wgt_motCtx_motNeur"]

# Sensory feedback delay (seconds)
# delay_fbk = spine_params["fbk_delay"]/1e3


# First ID sensory neurons
sensNeur_idSt = brain.firstIdSensNeurons  # 0
sensNeur_baseRate = spine_params["sensNeur_base_rate"]
sensNeur_gain = spine_params["sensNeur_kp"]


############################## MUSIC CONFIG ##############################

msc = MusicCfg()

# Compute the acceptable latency (AL) of this input port to make sure that
# Sum(ALs)>=Sum(ITIs). ITI stands for Inter Tick Intervals.
accLat = 2 * res - (res - msc.const / 1e3)
# If AL<0, set it to zero (this will satisfy the relationship above)
if accLat < 0:
    accLat = 0

firstId = 0  # First neuron taken care of by this MPI rank
nlocal = N * 2 * njt  # Number of neurons taken care of by this MPI rank

# Creation of MUSIC ports
# The MUSIC setup object is used to configure the simulation

indata = setup.publishEventInput("mot_cmd_in")

outdata = setup.publishEventOutput("fbk_out")

# NOTE: The actual neuron IDs from the sender side are LOST!!!
# By knowing how many joints and neurons, one should be able to retreive the
# function of each neuron population.


# Input handler function (it is called every time a spike is received)
def inhandler(t, indextype, channel_id):
    # Get the variable corrsponding to channel_id
    var_id = int(channel_id / (N * 2))
    # Get the neuron number within those associated to the variable
    tmp_id = channel_id % (N * 2)
    # Identify whether the neuron ID is from the positive otr negative population
    flagSign = tmp_id / N
    if flagSign < 1:  # Positive population
        spikes_pos[var_id].append([t, channel_id])
    else:  # Negative population
        spikes_neg[var_id].append([t, channel_id])
    # Just to handle possible errors
    if flagSign < 0 or flagSign >= 2:
        raise Exception("Wrong neuron number during reading!")


# Config of the input port
indata.map(inhandler, music.Index.GLOBAL, base=firstId, size=nlocal, accLatency=accLat)

# Config of the output port
outdata.map(music.Index.GLOBAL, base=firstId, size=nlocal)


################ SENSORY NEURONS

sn_p = []  # Positive sensory neurons
sn_n = []  # Negative sensory neurons
for i in range(njt):
    # Positive
    idSt_p = sensNeur_idSt + 2 * N * i
    tmp = SensoryNeuron(
        N, pos=True, idStart=idSt_p, bas_rate=sensNeur_baseRate, kp=sensNeur_gain
    )
    tmp.connect(outdata)  # Connect to output port
    sn_p.append(tmp)
    # Negative
    idSt_n = idSt_p + N
    tmp = SensoryNeuron(
        N, pos=False, idStart=idSt_n, bas_rate=sensNeur_baseRate, kp=sensNeur_gain
    )
    tmp.connect(outdata)  # Connect to output port
    sn_n.append(tmp)


######################## SETUP ARRAYS ################################

# Lists that will contain the positive and negative spikes
# Each element of the list corrspond to a variable to be controlled.
# Each variable is controlled by N*2 nuerons (N positive, N negative).
# These lists will be pupulated by the handler function while spikes are received.
spikes_pos = []
spikes_neg = []
for i in range(njt):
    spikes_pos.append([])
    spikes_neg.append([])

# Arrays that will contain the spike rates at each time instant
spkRate_pos = np.zeros([n_time, njt])
spkRate_neg = np.zeros([n_time, njt])
spkRate_net = np.zeros([n_time, njt])

# Sequence of position and velocities
pos = np.zeros([n_time, 3])  # End-effector space
vel = np.zeros([n_time, 2])
pos_j = np.zeros([n_time, njt])  # Joint space
vel_j = np.zeros([n_time, njt])

# Sequence of motor commands, perturbation and total input
inputCmd = np.zeros([n_time, njt])  # Input commands (from motor commands)
# perturb      = np.zeros([n_time,2])   # Perturbation (end-effector)
# perturb_j    = np.zeros([n_time,njt]) # Perturbation (joint)
inputCmd_tot = np.zeros([n_time, njt])  # Total input to dynamical system


######################## RUNTIME ##########################
# names = ["planner_p", "planner_n", "ffwd_p", "ffwd_n", "fbk_p", "fbk_n", "out_p", "out_n", "brainstem_p", "brainstem_n", "sn_p", "sn_n", "pred_p", "pred_n", "state_p", "state_n"]
# pops = [planner.pops_p, planner.pops_n, mc.ffwd_p, mc.ffwd_n, mc.fbk_p, mc.fbk_n, mc.out_p, mc.out_n, brain_stem_new_p, brain_stem_new_n, sn_p, sn_n, prediction_p, prediction_n, stEst.pops_p, stEst.pops_n]
# Function to copute spike rates within within a buffer
def computeRate(spikes, w, nNeurons, timeSt, timeEnd):
    count = 0
    rate = 0
    if len(spikes) > 0:
        tmp = np.array(spikes)
        idx = np.bitwise_and(tmp[:, 0] >= timeSt, tmp[:, 0] < timeEnd)
        count = w * tmp[idx, :].shape[0]  # Number of spiked by weight
        rate = count / ((timeEnd - timeSt) * nNeurons)
    return rate, count


# Start the runtime phase
runtime = music.Runtime(setup, res)
step = 0  # simulation step
errors = []
tickt = runtime.time()
save = False
while tickt < exp_duration:
    if not (step % 200):
        print(step)
    """
    if save:
        collapse_files_bullet(exp.pathData+"nest/", exp.names, njt)
        add_entry(exp)
        save = False
    """

    # Get bullet joint states
    bullet_robot.UpdateStats()

    # Position and velocity at the beginning of the timestep
    pos_j[step, :] = bullet_robot.JointPos(RobotArm1Dof.ELBOW_JOINT_ID)  # Joint space
    vel_j[step, :] = bullet_robot.JointVel(RobotArm1Dof.ELBOW_JOINT_ID)
    pos[step, :] = bullet_robot.EEPose()[0][0:3]  # End effector space. Convert to 2D
    vel[step, :] = bullet_robot.EEVel()[0][0:3:2]

    # After a certain number of trials I switch on the force field
    # The number of trials is defined by "ff_application" variable
    """
    if tickt >= ff_application*(timeMax+time_pause) and tickt <= ff_application*(timeMax+time_pause)+0.02:
        print('Added Force Field')
        k = exp.frcFld_k
    elif tickt >= ff_removal*(timeMax+time_pause) and tickt <= ff_removal*(timeMax+time_pause)+0.02:
        print('Removed Force Field')
        k = 0
    """

    # After completing the task and during the pause: initialize position and velocity
    # if tickt%(timeMax+time_pause) >= timeMax:
    # dynSys.pos = dynSys.inverseKin(exp.init_pos) # Initial condition (position)
    # dynSys.vel = np.array([0.0])             # Initial condition (velocity)
    # pass
    # else:
    # Send sensory feedback and compute input commands for this timestep
    buf_st = tickt - bufSize  # Start of buffer
    buf_ed = tickt  # End of buffer
    for i in range(njt):
        # Generate and send sensory feedback spikes given plan position
        sn_p[i].update(pos_j[step, i], res, tickt)
        sn_n[i].update(pos_j[step, i], res, tickt)
        # Compute input commands
        spkRate_pos[step, i], c = computeRate(spikes_pos[i], w, N, buf_st, buf_ed)
        spkRate_neg[step, i], c = computeRate(spikes_neg[i], w, N, buf_st, buf_ed)
        spkRate_net[step, i] = spkRate_pos[step, i] - spkRate_neg[step, i]
        inputCmd[step, i] = spkRate_net[step, i] / scale

        # perturb[step,:]      = pt.curledForceField(vel[step,:], angle, k)                     # End-effector forces
        # perturb_j[step,:]    = np.matmul( dynSys.jacobian(pos_j[step,:]) , perturb[step,:] )  # Torques
        inputCmd_tot[step, :] = inputCmd[
            step, :
        ]  # + perturb_j[step,:]                           # Total torques
        # print('inputCmd_tot[step,:]: ', inputCmd_tot[step,:])
        # Set joint torque
        bullet_robot.SetJointTorques(
            joint_ids=[RobotArm1Dof.ELBOW_JOINT_ID], torques=inputCmd_tot[step, :]
        )

        # Integrate dynamical system
        # print("simulo")
        bullet.Simulate(sim_time=res)

        ## At the end of each trial, compute error and store it
        if (
            tickt % time_trial == 0 and int(tickt / time_trial != 0)
        ) or tickt == exp_duration - res:
            error = pos_j[step, i] - tgt_pos
            print("Trial finished")
            print("Trial ", int(tickt / time_trial), ", error: ", error, "\n")
            errors.append(error)
            # p.resetJointState(
            #     bullet_robot._body_id, RobotArm1Dof.ELBOW_JOINT_ID, init_pos
            # )  # Restart trial from initial position

            if error < 0.3:
                print("Error inferior to 0.3")
                # save = True

    step = step + 1
    runtime.tick()
    tickt = runtime.time()
runtime.finalize()


########################### SAVING INTO DISK ###########################
def firstElement(elem):
    return elem[0]


# Spikes (of each neuron within the population for each joint)
for i in range(njt):

    ########### Motor commands (input from MUSIC)
    # Positive
    tmp_fnm_p = pthDat + "motNeur_inSpikes_j" + str(i) + "_p.txt"
    if len(spikes_pos[i]) > 0:
        spikes_pos[i].sort(key=firstElement)
        tmp_dat_p = np.array(spikes_pos[i])
        np.savetxt(tmp_fnm_p, tmp_dat_p, fmt="%3.4f\t%d", delimiter="\t")
    else:
        tmp_dat_p = np.array(spikes_pos[i])
        np.savetxt(tmp_fnm_p, tmp_dat_p)

    # Negative
    tmp_fnm_n = pthDat + "motNeur_inSpikes_j" + str(i) + "_n.txt"
    if len(spikes_neg[i]) > 0:
        spikes_neg[i].sort(key=firstElement)
        tmp_dat_n = np.array(spikes_neg[i])
        np.savetxt(tmp_fnm_n, tmp_dat_n, fmt="%3.4f\t%d", delimiter="\t")
    else:
        tmp_dat_n = np.array(spikes_neg[i])
        np.savetxt(tmp_fnm_n, tmp_dat_n)

    ########### Sensory neurons (output to MUSIC)

    # Positive
    tmp_fnm_p = pthDat + "sensNeur_outSpikes_j" + str(i) + "_p.txt"
    if len(sn_p[i].spike) > 0:
        sn_p[i].spike.sort(key=firstElement)
        tmp_dat_p = np.array(sn_p[i].spike)
        np.savetxt(tmp_fnm_p, tmp_dat_p, fmt="%3.4f\t%d", delimiter="\t")
    else:
        tmp_dat_p = np.array(sn_p[i].spike)
        np.savetxt(tmp_fnm_p, tmp_dat_p)

    # Negative
    tmp_fnm_n = pthDat + "sensNeur_outSpikes_j" + str(i) + "_n.txt"
    if len(sn_n[i].spike) > 0:
        sn_n[i].spike.sort(key=firstElement)
        tmp_dat_n = np.array(sn_n[i].spike)
        np.savetxt(tmp_fnm_n, tmp_dat_n, fmt="%3.4f\t%d", delimiter="\t")
    else:
        tmp_dat_n = np.array(sn_n[i].spike)
        np.savetxt(tmp_fnm_n, tmp_dat_n)

# Motor neuron spike rates (of each population for each joint)
np.savetxt(pthDat + "motNeur_rate_pos.csv", spkRate_pos, delimiter=",")
np.savetxt(pthDat + "motNeur_rate_neg.csv", spkRate_neg, delimiter=",")
np.savetxt(pthDat + "motNeur_rate_net.csv", spkRate_net, delimiter=",")

# Position and velocities (joint space)
np.savetxt(pthDat + "pos_real_joint.csv", pos_j, delimiter=",")
np.savetxt(pthDat + "vel_real_joint.csv", vel_j, delimiter=",")

# Position and velocities (end-effector space)
np.savetxt(pthDat + "pos_real_ee.csv", pos, delimiter=",")
np.savetxt(pthDat + "vel_real_ee.csv", vel, delimiter=",")

# Desired trajectory
np.savetxt(pthDat + "pos_des_ee.csv", trj_ee, delimiter=",")  # End-effector
np.savetxt(pthDat + "pos_des_joint.csv", trj, delimiter=",")  # Joints

# Motor commands
np.savetxt(pthDat + "inputCmd_des.csv", inputDes, delimiter=",")  # Desired torques
np.savetxt(
    pthDat + "inputCmd_motNeur.csv", inputCmd, delimiter=","
)  # Torques from motor neurons
np.savetxt(
    pthDat + "inputCmd_tot.csv", inputCmd_tot, delimiter=","
)  # Torques from motor neurons + perturbation
# np.savetxt( pthDat+"perturbation_ee.csv", perturb, delimiter=',' )   # Perturbation force in end-effector space
# np.savetxt( pthDat+"perturbation_j.csv", perturb_j, delimiter=',' )  # Perturbation torque


########################### PLOTTING ###########################
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
lgd = ["theta", "des"]
plt.figure()
plt.plot(time_tot, inputCmd)
# plt.plot(time,inputDes,linestyle=':')
plt.xlabel("time (s)")
plt.ylabel("motor commands (N)")
plt.legend(lgd)
if saveFig:
    plt.savefig(pathFig + cond + "motCmd.png")


# Joint space
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
wait_trj = np.ones(len(time_wait_vec)) * trj[steps_wait]
print(wait_trj)
wait_trj = np.concatenate((wait_trj, trj[steps_wait:]))
print(wait_trj)
plt.figure()
plt.plot(time_tot, pos_j, linewidth=3)
plt.plot(time_tot, wait_trj, linestyle=":", linewidth=3)
plt.xlabel("time (s)")
plt.ylabel("angle (rad)")
plt.legend(["actual", "desired"])
plt.ylim((0.0, 1.6))
if saveFig:
    # plt.savefig(pathFig+"position_joint.png")
    plt.savefig(f"{pathFig}position_joint_{timestamp}.png")
    # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/position_joint.png")

# End-effector space
plt.figure()
trial_delta = int((timeMax + time_wait) / res)
task_steps = int((timeMax + time_wait) / res)
errors = []
err_x = []
for trial in range(n_trial):
    start = trial * trial_delta
    print("start: ", start)
    end = start + task_steps - 1
    print("end: ", end)

    """'
    if trial < ff_application: # Only cerebellum
        style = 'k'
    else:
        style = 'r:'  # Cerebellum must compensate delay and Force field
    """
    style = "k"
    plt.plot(pos[start:end, 0], pos[start:end, 2], style)
    plt.plot(pos[end, 0], pos[end, 2], marker="x", color="k")
    # errors.append(np.sqrt((pos[end,0] -tgt_pos_ee[0,0])**2 + (pos[end,1] - tgt_pos_ee[1,0])**2))
    # err_x.append(pos[end,0] -tgt_pos_ee[0])
    print(
        "target position: ",
        tgt_pos,
        ", reached position: ",
        pos_j[-1],
        ", error: ",
        tgt_pos - pos_j[-1],
    )
    plt.plot(pos[start:end, 0], pos[start:end, 2], style, label="trajectory")
    plt.plot(pos[end, 0], pos[end, 2], marker="x", color="k", label="reached pos")
    # error_x = pos[end,0] -tgt_pos_ee[0]
    # error_y = pos[end,1] -tgt_pos_ee[1]
    # errors_xy = [error_x, error_y, np.array(errors[-1])]
    print(f"\n\n\n exp.init_pos_ee={exp.init_pos_ee}, exp.tgt_pos_ee={exp.tgt_pos_ee}")

    plt.plot(
        hand_at_zero[0],
        hand_at_zero[2],
        marker="x",
        color="blue",
        label="hand at zero",
    )
    plt.plot(
        hand_at_desired[0],
        hand_at_desired[2],
        marker=".",
        color="red",
        label="hand at desired",
    )
    plt.plot(
        hand_at_effective_start[0],
        hand_at_effective_start[2],
        marker=".",
        color="orange",
        label="hand_at_effective_start",
    )
    plt.plot(
        p.getLinkState(
            bullet_robot._body_id,
            RobotArm1Dof.HAND_LINK_ID,
            computeLinkVelocity=True,
        )[0][0],
        p.getLinkState(
            bullet_robot._body_id,
            RobotArm1Dof.HAND_LINK_ID,
            computeLinkVelocity=True,
        )[0][2],
        marker=".",
        color="green",
        label="final hand pos",
    )
    # plt.plot(
    #     p.getLinkState(
    #         bullet_robot._body_id,
    #         RobotArm1Dof.FOREARM_LINK_ID,
    #         computeLinkVelocity=True,
    #     )[0][0],
    #     p.getLinkState(
    #         bullet_robot._body_id,
    #         RobotArm1Dof.FOREARM_LINK_ID,
    #         computeLinkVelocity=True,
    #     )[0][1],
    #     marker=".",
    #     color="black",
    #     label="foreamr ",
    # )

    plt.axis("equal")
    plt.xlabel("position x (m)")
    plt.ylabel("position y (m)")
    plt.legend()
    if saveFig:
        # plt.savefig(pathFig+"position_ee.png")
        # plt.savefig("/home/alphabuntu/workspace/controller/complete_control/figures_thesis/cloop_nocereb/position_ee.png")
        plt.savefig(pathFig + f"position_ee_{timestamp}.png")

    plt.figure()
    plt.plot(errors)
    plt.xlabel("Trial")
    plt.ylabel("Error [m]")
    if saveFig:
        plt.savefig(pathFig + cond + "error_ee.png")

    # np.savetxt("error.txt",np.array(errors)*100)

# np.savetxt("error_xy.txt",np.array(errors_xy)*100)

# target_distance = np.sqrt((tgt_pos_ee[0] - init_pos_ee[0])**2 + (tgt_pos_ee[1] - init_pos_ee[1])**2)
# err_perc = [i/target_distance for i in errors]
# plt.figure()
# plt.plot(err_perc)
# plt.xlabel('Trial')
# plt.ylabel('Error [%]')
# if saveFig:
#     plt.savefig(pathFig+cond+"error_ee_perc.png")

# plt.figure()
# plt.plot(err_x)
# plt.xlabel('Trial')
# plt.ylabel('Horizontal error [m]')
# if saveFig:
#     plt.savefig(pathFig+cond+"error_ee_x.png")

# target_distance_x = abs(tgt_pos_ee[0] - init_pos_ee[0])
# err_x_perc = [i/target_distance_x for i in err_x]
# plt.figure()
# plt.plot(err_x)
# plt.xlabel('Trial')
# plt.ylabel('Horizontal error [%]')
# if saveFig:
#     plt.savefig(pathFig+cond+"error_ee_x_perc.png")


# np.save_file_fig(pathFig)
# Show sensory neurons
# for i in range(njt):
#     plotPopulation(time, sn_p[i], sn_n[i], title=lgd[i],buffer_size=0.015)

# plt.show()
