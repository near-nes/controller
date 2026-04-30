"""Smoke test: train the M1 e-prop network and verify the artifact.

Writes to $NEUROCONTROLLER_M1_ARTIFACTS_DIR, falling back to
tests/training/artifacts/m1/ for local runs.

Requires the dev container — needs NEST + custom_stdp_module.
"""

import os
from pathlib import Path

from motor_controller_model.config_schema import MotorControllerConfig
from motor_controller_model.m1_factory import get_m1_or_train

# n_iter is excluded from the config-match check in m1_factory, so reducing it
# does not cause a mismatch when the trial job loads the saved weights.
M1_OVERRIDES = {
    "task": {"n_iter": 2},
}

_FALLBACK = Path(__file__).parent / "artifacts" / "m1"


def _artifacts_dir() -> Path:
    if env := os.getenv("NEUROCONTROLLER_M1_ARTIFACTS_DIR"):
        return Path(env)
    return _FALLBACK


def test_train_m1():
    m1_dir = _artifacts_dir()
    m1_dir.mkdir(parents=True, exist_ok=True)

    cfg = MotorControllerConfig.model_validate(M1_OVERRIDES)
    get_m1_or_train(
        cfg,
        artifacts_dir=m1_dir,
        nest_module="custom_stdp_module",
        force_retrain=True,
    )

    assert (m1_dir / "trained_weights.npz").exists()
    assert (m1_dir / "config.yaml").exists()
