"""Smoke test: train the PFC trajectory generator and verify the artifact.

Vision training is skipped (requires the 1.2 GB image dataset). The shipped
vision artifacts are copied in so the full planner is usable after this test.

Writes to $NEUROCONTROLLER_PLANNER_ARTIFACTS_DIR, falling back to
tests/training/artifacts/pfc_planner/ for local runs.

Requires the dev container (torch CPU is sufficient — no NEST needed).
"""

import os
import shutil
from importlib.resources import files
from pathlib import Path

import numpy as np
import torch
from pfc_planner.config import PlannerParams
from pfc_planner.train_trajectory import train_trajectory_generator

# Intentionally tiny — goal is "training runs and artifact loads", not convergence.
PFC_TRAJ_OVERRIDES = dict(
    num_samples=64,
    num_epochs=2,
    batch_size=16,
)

_FALLBACK = Path(__file__).parent / "artifacts" / "pfc_planner"


def _artifacts_dir() -> Path:
    if env := os.getenv("NEUROCONTROLLER_PLANNER_ARTIFACTS_DIR"):
        return Path(env)
    return _FALLBACK


def _seed_vision_artifacts(pfc_dir: Path) -> None:
    shipped = Path(str(files("neurocontroller").joinpath("artifacts/pfc_planner")))
    for fname in ("trained_gle_planner.pth", "trained_gle_planner.json"):
        shutil.copy2(shipped / fname, pfc_dir / fname)


def test_train_planner():
    pfc_dir = _artifacts_dir()
    pfc_dir.mkdir(parents=True, exist_ok=True)

    np.random.seed(0)
    torch.manual_seed(0)
    _seed_vision_artifacts(pfc_dir)

    train_trajectory_generator(
        PlannerParams(),
        generator_type="gle",
        project_root=pfc_dir,
        model_dir=pfc_dir,
        **PFC_TRAJ_OVERRIDES,
    )

    assert (pfc_dir / "trained_gle_trajectory_generator.pth").exists()
    assert (pfc_dir / "trained_gle_planner.pth").exists()
