"""Smoke test: run a 1-trial closed-loop sim using previously trained artifacts.

Expects both NEUROCONTROLLER_M1_ARTIFACTS_DIR and
NEUROCONTROLLER_PLANNER_ARTIFACTS_DIR to point at directories containing
trained weights (produced by test_train_m1 and test_train_planner).
Falls back to tests/training/artifacts/{m1,pfc_planner}/ for local runs.

Requires the dev container — needs NEST + custom_stdp_module + nrp-core.
"""

import os
from pathlib import Path

import pytest

_ARTIFACTS = Path(__file__).parent / "artifacts"
_FALLBACK_M1 = _ARTIFACTS / "m1"
_FALLBACK_PFC = _ARTIFACTS / "pfc_planner"


def _check_artifacts(m1_dir: Path, pfc_dir: Path) -> None:
    missing = []
    for p in [
        m1_dir / "trained_weights.npz",
        m1_dir / "config.yaml",
        pfc_dir / "trained_gle_trajectory_generator.pth",
        pfc_dir / "trained_gle_planner.pth",
    ]:
        if not p.exists():
            missing.append(str(p))
    if missing:
        pytest.skip(
            "Trained artifacts not found — run test_train_m1 and test_train_planner first.\n"
            + "\n".join(f"  missing: {p}" for p in missing)
        )


def test_run_trial(monkeypatch, tmp_path):
    m1_dir = Path(os.getenv("NEUROCONTROLLER_M1_ARTIFACTS_DIR", _FALLBACK_M1))
    pfc_dir = Path(os.getenv("NEUROCONTROLLER_PLANNER_ARTIFACTS_DIR", _FALLBACK_PFC))

    _check_artifacts(m1_dir, pfc_dir)

    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    # Set env vars BEFORE importing neurocontroller — paths.RUNS_DIR is a
    # module-level constant captured at import time.
    monkeypatch.setenv("RUNS_PATH", str(runs_dir))
    monkeypatch.setenv("NEUROCONTROLLER_M1_ARTIFACTS_DIR", str(m1_dir))
    monkeypatch.setenv("NEUROCONTROLLER_PLANNER_ARTIFACTS_DIR", str(pfc_dir))

    from neurocontroller.nrp_start_sim import run_trial

    run_id = run_trial(parent_id="", label="train-test")
    assert run_id

    run_dir = runs_dir / run_id
    assert run_dir.is_dir()
    assert any(run_dir.glob("params*.json"))
