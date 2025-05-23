"""Experiment"""

__authors__ = "Cristiano Alessandro"
__copyright__ = "Copyright 2021"
__credits__ = ["Cristiano Alessandro"]
__license__ = "GPL"
__version__ = "1.0.1"


import math
import sys

import numpy as np

# Just to get the following imports right!
sys.path.insert(1, "../")

# import perturbation as pt
import os

from plant.robot1j import Robot1J

SEED = 12345


####################################################################
class Experiment:

    def __init__(self):
        self._init_joint_angle = 0
        self._tgt_joint_angle = 90

        # Perturbation
        alpha = 0  # np.arctan(self._tgt_pos[:,1]/self._tgt_pos[:,0])/np.pi*180
        left = 180 - alpha
        right = -alpha
        self._frcFld_angle = (
            right  # Angle of the perturbation force wrt movement velocity
        )
        self._frcFld_k = 2  # Gain of the perturbation force wrt movement velocity
        self._ff_application = (
            1e6  # Trial at which the Force Field is applied (1e6 = no force field)
        )
        self._ff_removal = (
            1e6  # Trial at which the Force Field is removed for extinction
        )

        # Dynamical system
        self._robot_spec = {
            "mass": np.array([1.89]),
            "links": np.array([0.31]),
            "I": np.array([0.00189]),
        }  # 0.00189
        self._dynSys = Robot1J(robot=self._robot_spec)
        self._dynSys.pos = [self.init_pos_angle]
        self._dynSys.vel = np.array([0.0])  # with zero initial velocity

        # At which trial Cerebellum connected to StateEstimator
        self._cerebellum_application_forw = 1e6

        self._cerebellum_application_inv = 1e6

    @property
    def dynSys(self):
        return self._dynSys

    @property
    def frcFld_angle(self):
        return self._frcFld_angle

    @property
    def frcFld_k(self):
        return self._frcFld_k

    @property
    def ff_application(self):
        return self._ff_application

    @property
    def ff_removal(self):
        return self._ff_removal

    @property
    def cerebellum_application_forw(self):
        return self._cerebellum_application_forw

    @property
    def cerebellum_application_inv(self):
        return self._cerebellum_application_inv

    @property
    def init_pos_angle(self):
        """returns _init_pos_angle IN RADIANS"""
        return math.radians(self._init_joint_angle)

    @property
    def tgt_pos_angle(self):
        """returns _init_pos_angle IN RADIANS"""
        return math.radians(self._tgt_joint_angle)


####################################################################
class Simulation:

    def __init__(self):

        # Nest resolution (milliseconds)
        self._resolution = 0.1

        # Waiting time before movement execution (milliseconds)
        self._time_prep = 50.0
        # time_prep [150] -> time_trial [500] -> time_wait [350]

        # Simulation time (milliseconds)
        self._time_move = 250.0

        # Pause after movement (milliseconds)
        self._time_post = 100.0

        # Number of trials
        self._n_trials = 2

    @property
    def resolution(self):
        return self._resolution

    @property
    def time_prep(self):
        return self._time_prep

    @property
    def time_move(self):
        return self._time_move

    @property
    def time_post(self):
        return self._time_post

    @property
    def n_trials(self):
        return self._n_trials

    @property
    def duration_single_trial_ms(self):
        return self.time_prep + self.time_move + self.time_post

    @property
    def duration_single_trial_s(self):
        return self.duration_single_trial_ms / 1000

    @property
    def total_duration_all_trials_ms(self):
        return self.duration_single_trial_ms * self.n_trials

    @property
    def total_steps_single_trial(self):
        return self.duration_single_trial_s / self.resolution


####################################################################
class Brain:

    def __init__(self):

        # Number of neurons for each subpopulation (positive/negative)
        self._nNeurPop = 50

        # Which joint is controlled by the cerebellum (0 = x, 1 = y)
        self._cerebellum_controlled_joint = 0

        # HDF5 containing cerebellar scaffold
        self._filename_h5 = "mouse_cereb_microzones_nest.hdf5"

        # JSON configuration file
        self._filename_config = "microzones_nest.yaml"

        # self.initPlanner()        # Initialize planner settings
        self.initMotorCortex()  # Initialize motor cortex settings
        # self.initStateEstimator() # Initialize state estimator
        self.initSpine()  # Initialize spinal cord settings

        # self._connections = {
        #     "wgt_plnr_mtxFbk"  :  1.0, # Connection weight (excitatory) between Planner and Motor Cortex FBK
        #     "wgt_stEst_mtxFbk" : -1.0, # Connection weight (inhibitory) between State Estimator and Motor Cortex FBK
        #     "wgt_spine_stEst"  :  1.0  # Connection weigth (excitatory) between Spine and State Estimator
        # }

    # def initPlanner(self):

    # # Replanning gain
    # self._kpl = 0.5

    # # Population parameteres
    # self._plan_param = {
    #     "base_rate":  0.0, # Base rate
    #     "kp":      1200.0  # Gain
    #     }

    def initMotorCortex(self):

        # If true, motor cortex computes precise motor commands using inv. dynamics
        self._precCtrl = False

        # self._motCtx_param = {
        #     "ffwd_base_rate":  0.0, # Feedforward neurons
        #     "ffwd_kp":        10.0,
        #     "fbk_base_rate":   0.0, # Feedback neurons
        #     "fbk_kp":          0.3,
        #     "out_base_rate":   0.0, # Output neurons
        #     "out_kp":          1.0,
        #     "wgt_ffwd_out":    1.0, # Connection weight from ffwd to output neurons (must be positive)
        #     "wgt_fbk_out":     1.0, # Connection weight from fbk to output neurons (must be positive)
        #     "buf_sz":         20.0  # Size of the buffer to compute spike rate in basic_neurons (ms)
        #     }

    # def initStateEstimator(self):
    # Not used for StateEstimator Massimo TODO

    # self._k_prediction = 0.0     # Reiability of the prediction input of the state estimator
    # self._k_sensory    = 1.0     # Reiability of the sensory feedback input of the state estimator

    # self._stEst_param = {
    #     "out_base_rate":  0.0,   # Summation neurons (i.e. basic_neurons)
    #     "out_kp":         1.0,   # Gain of the output neurons
    #     "wgt_scale":      1.0,   # Scale of connection weight from input to output populations (must be positive)
    #     "buf_sz":        10.0    # Size of the buffer to compute spike rate in basic_neurons (ms)
    #     }

    def initSpine(self):

        self._firstIdSensNeurons = (
            0  # First ID of the sensory neurons (keep it at zero)
        )

        # self._spine_param = {
        #     "wgt_motCtx_motNeur" : 1.0, # Weight motor cortex - motor neurons
        #     "wgt_sensNeur_spine" : 1.0, # Weight sensory neurons - spine
        #     "sensNeur_base_rate":  0.0, # Sensory neurons baseline rate
        #     "sensNeur_kp":      1200.0, # Sensory neurons gain
        #     "fbk_delay":          0.1 # 80.0 It cannot be less than resolution (ms) [0.1 oppure 80.0]
        #     }

    @property
    def nNeurPop(self):
        return self._nNeurPop

    @property
    def cerebellum_controlled_joint(self):
        return self._cerebellum_controlled_joint

    @property
    def filename_h5(self):
        return self._filename_h5

    @property
    def filename_config(self):
        return self._filename_config

    # @property
    # def connections(self):
    #     return self._connections

    # @property
    # def plan_param(self):
    #     return self._plan_param

    # @property
    # def kpl(self):
    #     return self._kpl

    # @property
    # def k_prediction(self):
    #     return self._k_prediction

    # @property
    # def k_sensory(self):
    #     return self._k_sensory

    # @property
    # def stEst_param(self):
    #     return self._stEst_param

    # @property
    # def motCtx_param(self):
    #     return self._motCtx_param

    @property
    def precCtrl(self):
        return self._precCtrl

    @property
    def firstIdSensNeurons(self):
        return self._firstIdSensNeurons

    # @property
    # def spine_param(self):
    #     return self._spine_param


####################################################################
class MusicCfg:

    def __init__(self):
        self._const = 1e-6  # Constant to subtract to avoid rounding errors (ms)
        self._input_latency = 0.0001  # seconds

    @property
    def input_latency(self):
        return self._input_latency

    @property
    def const(self):
        return self._const
