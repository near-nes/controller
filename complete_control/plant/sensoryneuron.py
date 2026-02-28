"""Sensory neuron class"""

__authors__ = "Cristiano Alessandro"
__copyright__ = "Copyright 2021"
__credits__ = ["Cristiano Alessandro"]
__license__ = "GPL"
__version__ = "1.0.1"

import numpy as np
from config.core_models import SimulationParams

SEED = SimulationParams.get_default_seed()
np.random.seed(SEED)


class SensoryNeuron:

    def __init__(
        self,
        numNeurons,
        pos=True,
        idStart=0,
        bas_rate=0.0,
        kp=1.0,
        res=1,
    ):

        self.numNeurons = numNeurons
        self.baseline_rate = bas_rate
        self.gain = kp
        self._spike = []
        self.pos = pos

        # Set IDs starting from idStart
        id_vect = np.zeros(shape=numNeurons)
        for i in range(numNeurons):
            id_vect[i] = i + idStart
        self.pop = id_vect
        self.res = res
        self.rng = np.random.default_rng(SEED)

    @property
    def spike(self):
        return self._spike

    # Update theoretical spike rate based on input signal, and generate spikes
    def update(self, signal, simTime):
        lmd = self.lam(signal) * self.res
        nEv = self.rng.poisson(lam=lmd, size=(self.numNeurons))

        for i in range(self.numNeurons):
            if (nEv[i]) > 0:
                self.spike.append([simTime, self.pop[i]])

    def lam(self, signal):
        if (self.pos and signal < 0) or (not self.pos and signal >= 0):
            signal = 0
        rate = self.baseline_rate + self.gain * abs(signal)
        return rate
