"""Generic class for a population of neuron."""

__authors__ = "Alberto Antonietti and Cristiano Alessandro"
__copyright__ = "Copyright 2020"
__credits__ = ["Alberto Antonietti and Cristiano Alessandro"]
__license__ = "GPL"
__version__ = "1.0.1"


from pathlib import Path

import numpy as np
import pandas as pd
import structlog
from neural.nest_adapter import nest
from neural.neural_models import PopulationSpikes, RecordingManifest

_log = structlog.get_logger(__name__)


############################ POPULATION VIEW #############################
class PopView:
    def __init__(self, pop, to_file=False, label=None):
        self.pop = pop
        self._label = label if label else None
        self._to_file = to_file
        self._detector_initialized = False

        if to_file and label:
            self._initialize_detector(label)
        elif to_file and not label:
            # Defer detector initialization until label is set
            self.detector = None
        else:  # to_file=False
            self.detector = self._create_connect_spike_detector(pop)

        self.neuron_model = nest.GetStatus(pop, "model")[0]
        self.gids = nest.GetStatus(pop, "global_id")

    def _initialize_detector(self, label):
        param_file = {"record_to": "ascii", "label": label}
        self.detector = self._create_connect_spike_detector(self.pop, **param_file)
        # nest will create file(s) for this recorder and write the names to
        # self.detector.get("filenames"); once data is collapsed to a single file
        # for usability, this property will hold the filename
        self.filepath: Path | None = None
        self._detector_initialized = True

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value
        # If to_file was requested but detector not yet initialized, do it now
        if self._to_file and not self._detector_initialized and value:
            self._initialize_detector(value)

    def collect(self, dir: Path, comm=None):
        if comm is None or nest.Rank() == 0:
            name = self.label
            file_list = [
                i
                for i in dir.iterdir()
                if i.name.startswith(name) and i.suffix != ".json"
            ]
            senders = []
            times = []
            combined_data = []

            for f in file_list:
                with open(dir / f, "r") as fd:
                    lines = fd.readlines()
                    for line in lines:
                        if line.startswith("#") or line.startswith("sender"):
                            continue
                        combined_data.append(line.strip())
            unique_lines = list(set(combined_data))

            for line in unique_lines:
                sender, time = line.split()
                senders.append(int(sender))
                times.append(float(time))

            pop_spikes = PopulationSpikes(
                label=name,
                gids=np.array(self.gids),
                senders=np.array(senders),
                times=np.array(times),
                population_size=len(self.gids),
                neuron_model=self.neuron_model,
            )

            complete_file = dir / (name + ".json")
            with open(complete_file, "w") as wfd:
                wfd.write(pop_spikes.model_dump_json(indent=4))

            self.filepath = complete_file
            for f in file_list:
                f.unlink()
            return pop_spikes
        else:
            return None

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
