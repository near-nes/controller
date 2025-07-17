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
        music_index_strategy=None,
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
        self._pop = id_vect
        self.res = res
        self.rng = np.random.default_rng(SEED)

        if music_index_strategy is not None:
            # using MUSIC
            self.outPort = []
            self.music_index_strategy = music_index_strategy

    @property
    def spike(self):
        return self._spike

    def connect(self, port):
        self.outPort = port

    # Update theoretical spike rate based on input signal, and generate spikes
    def update(self, signal, simTime):
        lmd = self.lam(signal)
        nEv = self.rng.poisson(lam=lmd, size=(self.numNeurons))

        for i in range(self.numNeurons):
            if (nEv[i]) > 0:
                self.spike.append([simTime, self.pop[i]])
                if self.outPort:
                    self.outPort.insertEvent(
                        simTime, self.pop[i], self.music_index_strategy
                    )
                else:
                    # print("Sensory neuron "+str(self.pop)+" not connected!")
                    pass

    def lam(self, signal):
        if (self.pos and signal < 0) or (not self.pos and signal >= 0):
            signal = 0
        rate = self.baseline_rate + self.gain * abs(signal)
        return rate * self.res
