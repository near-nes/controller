from pathlib import Path
from typing import ClassVar, Dict, List, Tuple

import structlog
from pydantic import BaseModel

from .plant_utils import JointData

_log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


class PlantPlotData(BaseModel):
    """Holds all data needed for plotting."""

    joint_data: List[JointData]
    errors_per_trial: List[float]
    init_hand_pos_ee: List[float]
    trgt_hand_pos_ee: List[float]

    model_config: ClassVar = {
        "arbitrary_types_allowed": True,
    }

    def save(self, params_path: Path):
        """Saves all collected simulation data to a single JSON file."""
        _log.info(f"Saving all simulation data to {params_path}")
        with open(params_path, "w") as f:
            f.write(self.model_dump_json(indent=2))
        _log.info("Finished saving all data.")

    @classmethod
    def load(cls, params_path: Path):
        """Loads the main plant data model from a JSON file."""
        _log.info(f"Loading plant data from {params_path}")
        with open(params_path, "r") as f:
            return cls.model_validate_json(f.read())
