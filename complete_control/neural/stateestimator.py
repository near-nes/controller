"""Motor cortex class"""

__authors__ = "Cristiano Alessandro and Massimo Grillo"
__copyright__ = "Copyright 2021"
__credits__ = ["Cristiano Alessandro and Massimo Grillo"]
__license__ = "GPL"
__version__ = "1.0.1"

import structlog
from neural.nest_adapter import nest

from .population_view import PopView

_log = structlog.get_logger("neural.StateEstimator")


class StateEstimator_mass:

    ############## Constructor  ##############
    def __init__(self, numNeurons, numJoints, time_vect, **kwargs):

        # Numerosity of each subpopulation
        self._numNeuronsPop = numNeurons

        # General parameters of neurons
        self._param_neurons = {
            "kp": 1.0,  # Gain
            "base_rate": 0.0,  # Baseline rate
            "buffer_size": 5.0,  # Size of the buffer
            "N_fbk": 50,
            "N_pred": 50,
            "fbk_bf_size": 2500,
            "pred_bf_size": 2500,
        }
        self.param_neurons.update(kwargs)

        # Create populations
        self.pops_p = []
        self.pops_n = []
        for i in range(numJoints):

            tmp_pop_p = nest.Create("state_neuron_nestml", numNeurons)
            nest.SetStatus(tmp_pop_p, self._param_neurons)
            nest.SetStatus(tmp_pop_p, {"pos": True})
            self.pops_p.append(
                PopView(tmp_pop_p, time_vect, to_file=True, label="state_p")
            )

            tmp_pop_n = nest.Create("state_neuron_nestml", numNeurons)
            nest.SetStatus(tmp_pop_n, self._param_neurons)
            nest.SetStatus(tmp_pop_n, {"pos": False})  # change here: it was tmp_pop_p ?
            self.pops_n.append(
                PopView(tmp_pop_n, time_vect, to_file=True, label="state_n")
            )

        params = [
            "kp",
            "base_rate",
            "buffer_size",
            "N_fbk",
            "N_pred",
            "fbk_bf_size",
            "pred_bf_size",
            "receptor_types",
            "var_fbk",
        ]
        state_status = nest.GetStatus(tmp_pop_p[:1], params)[0]

        # print(f"State params: {state_status}")

    @property
    def numNeuronsPop(self):
        return self._numNeuronsPop

    @property
    def param_neurons(self):
        return self._param_neurons


class StateEstimator:

    ############## Constructor (plant value is just for testing) ##############
    def __init__(
        self,
        numNeurons,
        time_vect,
        plant,
        kpred=0.0,
        ksens=1.0,
        pathData="./data/",
        **kwargs,
    ):

        self._numNeuronsPop = numNeurons

        self._kpred = kpred  # Weighting coefficient for predicted sensory information
        self._ksens = ksens  # Weighting coefficient for actual sensory information

        # General parameters of neurons
        self._param_neurons = {
            "out_base_rate": 0.0,  # Summation neurons
            "out_kp": 1.0,
            "wgt_scale": (
                1.0
            ),  # Scale of connection weight from input to output populations (must be positive)
            "buf_sz": (
                10.0  # Size of the buffer to compute spike rate in basic_neurons (ms)
            ),
        }
        self.param_neurons.update(kwargs)

        # Compute weigths
        wgt_pred_out, wgt_sens_out = self.computeWeights(self.kpred, self.ksens)
        self.param_neurons["wgt_pred_out"] = wgt_pred_out
        self.param_neurons["wgt_sens_out"] = wgt_sens_out

        # Initialize network
        nJt = plant.numVariables()
        self.init_neurons(
            self.numNeuronsPop, self.param_neurons, nJt, time_vect, pathData
        )

    # Compute connection weigths from input to output populations
    def computeWeights(self, kpred, ksens):
        wgt_pred_out, wgt_sens_out = self.bayesInt(kpred, ksens)
        scale = self.param_neurons["wgt_scale"]
        wgt_pred_out = scale * wgt_pred_out
        wgt_sens_out = scale * wgt_sens_out
        return wgt_pred_out, wgt_sens_out

    # TODO
    # Update connection weigths
    def updateWeigths(self, kpred, ksens):
        self.kpred = kpred
        self.ksens = ksens
        wgt_pred_out, wgt_sens_out = self.computeWeights(kpred, ksens)
        print("Weights update not implemented yet!")
        # TODO: update weigths

    # Bayesian integration
    def bayesInt(self, varPred, varSens):
        varTot = varPred + varSens
        wPred = varPred / varTot
        wSens = varSens / varTot
        return wPred, wSens

    ######################## Initialize neural network #########################
    def init_neurons(self, numNeurons, params, numJoints, time_vect, pathData):

        par_out = {"base_rate": params["out_base_rate"], "kp": params["out_kp"]}

        buf_sz = params["buf_sz"]

        self.pred_p = []
        self.pred_n = []
        self.sens_p = []
        self.sens_n = []
        self.out_p = []
        self.out_n = []

        res = time_vect[1] - time_vect[0]

        # Create populations
        for i in range(numJoints):

            ############ PREDICTION POPULATION ############

            # Positive population (joint i)
            tmp_pop_p = nest.Create("parrot_neuron", numNeurons)
            self.pred_p.append(PopView(tmp_pop_p, time_vect))

            # Negative population (joint i)
            tmp_pop_n = nest.Create("parrot_neuron", numNeurons)
            self.pred_n.append(PopView(tmp_pop_n, time_vect))

            ############ SENSORY FEEDBACK POPULATION ############

            # Positive population (joint i)
            tmp_pop_p = nest.Create("parrot_neuron", numNeurons)
            self.sens_p.append(PopView(tmp_pop_p, time_vect))

            # Negative population (joint i)
            tmp_pop_n = nest.Create("parrot_neuron", numNeurons)
            self.sens_n.append(PopView(tmp_pop_n, time_vect))

            ############ OUTPUT POPULATION ############

            # Positive population (joint i)
            tmp_pop_p = nest.Create("basic_neuron", n=numNeurons, params=par_out)
            nest.SetStatus(tmp_pop_p, {"pos": True, "buffer_size": buf_sz})
            self.out_p.append(PopView(tmp_pop_p, time_vect))

            # Negative population (joint i)
            tmp_pop_n = nest.Create("basic_neuron", n=numNeurons, params=par_out)
            nest.SetStatus(tmp_pop_n, {"pos": False, "buffer_size": buf_sz})
            self.out_n.append(PopView(tmp_pop_n, time_vect))

            ###### CONNECT FFWD AND FBK POULATIONS TO OUT POPULATION ######
            # Populations of each joint are connected together according to connection
            # rules and network topology. There is no connections across joints.

            self.pred_p[i].connect(
                self.out_p[i], rule="one_to_one", w=params["wgt_pred_out"], d=res
            )
            self.pred_p[i].connect(
                self.out_n[i], rule="one_to_one", w=params["wgt_pred_out"], d=res
            )
            self.pred_n[i].connect(
                self.out_p[i], rule="one_to_one", w=-params["wgt_pred_out"], d=res
            )
            self.pred_n[i].connect(
                self.out_n[i], rule="one_to_one", w=-params["wgt_pred_out"], d=res
            )

            self.sens_p[i].connect(
                self.out_p[i], rule="one_to_one", w=params["wgt_sens_out"], d=res
            )
            self.sens_p[i].connect(
                self.out_n[i], rule="one_to_one", w=params["wgt_sens_out"], d=res
            )
            self.sens_n[i].connect(
                self.out_p[i], rule="one_to_one", w=-params["wgt_sens_out"], d=res
            )
            self.sens_n[i].connect(
                self.out_n[i], rule="one_to_one", w=-params["wgt_sens_out"], d=res
            )

    ######################## Getters and Setters #########################

    @property
    def numNeuronsPop(self):
        return self._numNeuronsPop

    @property
    def kpred(self):
        return self._kpred

    @property
    def ksens(self):
        return self._ksens

    @property
    def param_neurons(self):
        return self._param_neurons

    @kpred.setter
    def kpred(self, value):
        self._kpred = value

    @ksens.setter
    def ksens(self, value):
        self._ksens = value
