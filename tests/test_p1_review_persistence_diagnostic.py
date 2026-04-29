import json
from pathlib import Path

import scripts.run_p1_review_persistence_diagnostic as diag


def _write_payload(tmp_path: Path) -> Path:
    p = tmp_path / "seed.json"
    p.write_text(json.dumps({"records": [{"forecast_probability": 0.7, "outcome": "YES"}]}), encoding="utf-8")
    return p


def _receipt(*, cycle_status="REVIEW_REQUIRED", confidence=0.2, drift_alerts=None, dominance_ratio=1.0, p0=0, p1=1, disp=0, total=3):
    return {
        "cycle_status": cycle_status,
        "calibration": {"mean_brier": 0.07},
        "fusion": {"confidence": confidence, "drift_alerts": drift_alerts or [], "dominance_ratio": dominance_ratio},
        "operator_queue": {"p0_count": p0, "p1_count": p1},
        "proof_state_set": {"display_allowed_count": disp, "total_items": total},
        "execution_triggered": False,
        "runtime_mutation": False,
        "authority_leak_detected": False,
    }


def test_deterministic_output(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt())
    a = diag.run_p1_review_persistence_diagnostic(str(seed), cycles=5)
    b = diag.run_p1_review_persistence_diagnostic(str(seed), cycles=5)
    assert a == b


def test_structure_and_safety(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt())
    out = diag.run_p1_review_persistence_diagnostic(str(seed), cycles=3)
    assert out["schema_version"] == "ABXP1ReviewPersistenceDiagnostic.v1"
    assert set(out["summary"].keys()) == {"avg_brier", "avg_confidence", "pass_count", "review_required_count", "blocked_count", "max_p0", "max_p1", "dominance_max"}
    assert set(out["p1_reason_counts"].keys()) == {"low_confidence_fusion", "dominance_imbalance", "proof_visibility_block", "operator_policy_review", "classifier_review_flag", "other"}
    assert out["safety_flags"] == {"execution_triggered": False, "runtime_mutation": False, "authority_leak_detected": False}


def test_driver_precedence_proof_visibility(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt(confidence=0.1, p1=1, disp=1, total=3))
    out = diag.run_p1_review_persistence_diagnostic(str(seed), cycles=10)
    assert out["dominant_p1_driver"] == "PROOF_VISIBILITY_PARTIAL"


def test_low_confidence_trigger(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt(confidence=0.4, drift_alerts=["LOW_CONFIDENCE"], disp=3, total=3))
    out = diag.run_p1_review_persistence_diagnostic(str(seed), cycles=6)
    assert out["p1_reason_counts"]["low_confidence_fusion"] == 6
    assert out["dominant_p1_driver"] == "LOW_CONFIDENCE_THRESHOLD"


def test_proof_visibility_trigger(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt(confidence=0.9, p1=0, disp=1, total=3))
    out = diag.run_p1_review_persistence_diagnostic(str(seed), cycles=6)
    assert out["p1_reason_counts"]["proof_visibility_block"] == 6
    assert out["dominant_p1_driver"] == "PROOF_VISIBILITY_PARTIAL"
