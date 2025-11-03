"""Generic class for a population of neuron."""

__authors__ = "Alberto Antonietti and Cristiano Alessandro"
__copyright__ = "Copyright 2020"
__credits__ = ["Alberto Antonietti and Cristiano Alessandro"]
__license__ = "GPL"
__version__ = "1.0.1"


from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import structlog
from neural.nest_adapter import nest

_log = structlog.get_logger(__name__)


############################ POPULATION VIEW #############################
class PopView:
    """
    Population View Class

    Wrapper around neural populations for visualization and analysis

    Attributes
    ----------
    pop : nest.NodeCollection
        The neural population being monitored
    detector : nest.NodeCollection
        Spike detector connected to the population
    total_n_events : int
        Counter for total number of spike events
    rates_history : list
        History of firing rates across trials
    time_vect : array-like
        Time vector for the simulation
    trial_len : float
        Length of each trial
    """

    def __init__(self, pop, time_vect=None, to_file=False, label=""):
        """
        Initialize PopulationView object to monitor spiking activity.
        Args:
            pop: Population to monitor.
            time_vect: Time vector for simulation.
            to_file (bool, optional): Flag to save data to file. Defaults to False.
            label (str, optional): Label for file saving. Required if to_file=True. Defaults to "".
        Raises:
            Exception: If to_file=True and no label provided.
        """

        self.pop = pop
        self.label = None
        if to_file:
            if label == "":
                raise Exception("To save into file, you need to specify a label")
            self.label = label
            param_file = {"record_to": "ascii", "label": label}
            self.detector = self._create_connect_spike_detector(pop, **param_file)
            # nest will create file(s) for this recorder and write the names to
            # self.detector.get("filenames"); once data is collapsed to a single file
            # for usability, this property will hold the filename
            self.filepath: Path | None = None
        else:
            self.detector = self._create_connect_spike_detector(pop)

        self.total_n_events = 0
        self.rates_history = []

    def collect(self):
        # TODO!
        _log.debug(f"{self.label} collect called!")

    def _create_connect_spike_detector(self, pop, **kwargs):
        spike_detector = nest.Create("spike_recorder")
        nest.SetStatus(spike_detector, params=kwargs)
        nest.Connect(pop, spike_detector)
        return spike_detector

    def connect(self, other, rule="one_to_one", w=1.0, d=0.1):
        nest.Connect(self.pop, other.pop, rule, syn_spec={"weight": w, "delay": d})

    def get_spike_events(self):
        spike_detector = self.detector
        # Get metadata about the recorder
        metadata = nest.GetStatus(spike_detector)

        if metadata.get("record_to") == "memory":
            dSD = nest.GetStatus(spike_detector, "events")
            evs = dSD["senders"]
            ts = dSD["times"]
            return evs, ts

        elif metadata.get("record_to") == "ascii":
            if not self.filepath:
                # assume collapse hasn't been called yet
                raise NotImplementedError(
                    "not ready to handle non-collapsed objects..."
                )
                # if not metadata.get("filenames"):
                #     return [], []
                # filepath = Path(metadata.get("filenames")[0])
            else:
                filepath = self.filepath

            # Check if the file exists
            if not filepath.exists():
                raise FileNotFoundError(
                    f"Recording file not found: {filepath}\nDid you call simulate()?"
                )

            # Read the file (skip the first two lines which are comments)
            df = pd.read_csv(filepath, sep="\t", comment="#")

            # Extract senders and times (convert ms to ms if time_in_steps is False)
            evs = df["sender"].values

            # Check if times are in milliseconds or steps
            if "time_ms" in df.columns:
                ts = df["time_ms"].values
            elif "time_step" in df.columns:
                ts = df["time_step"].values
            else:
                raise ValueError("Cannot find time column in the recording file")

            return evs, ts

        else:
            raise NotImplementedError(
                f"Unknown recording backend: {metadata.get('record_to')}"
            )
