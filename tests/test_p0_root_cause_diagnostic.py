import json
from pathlib import Path

import scripts.run_p0_root_cause_diagnostic as diag


def _write_payload(tmp_path: Path) -> Path:
    p = tmp_path / "seed.json"
    p.write_text(json.dumps({"records": [{"forecast_probability": 0.7, "outcome": "YES"}]}), encoding="utf-8")
    return p


def _receipt(*, cal_status="PASS", gate="PASS", sample=3, not_comp=0, resolved=3, total=3, p0=1):
    return {
        "calibration": {
            "calibration_drift_status": cal_status,
            "promotion_gate_status": gate,
            "sample_size": sample,
        },
        "operator_queue": {
            "p0_count": p0,
            "items": [{"priority": "P0", "review_id": "calibration.requires_review"}] if p0 else [],
        },
        "proof_state_set": {
            "items": [{"operator_review_item_id": "calibration.requires_review"}] if p0 else []
        },
        "not_computable_count": not_comp,
        "resolved_count": resolved,
        "input_record_count": total,
        "execution_triggered": False,
        "runtime_mutation": False,
        "authority_leak_detected": False,
    }


def test_deterministic_output(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt(cal_status="FAIL", gate="FAIL"))
    a = diag.run_p0_root_cause_diagnostic(str(seed), cycles=6)
    b = diag.run_p0_root_cause_diagnostic(str(seed), cycles=6)
    assert a == b


def test_json_shape_and_safety(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt())
    out = diag.run_p0_root_cause_diagnostic(str(seed), cycles=3)
    assert out["schema_version"] == "ABXP0RootCauseDiagnostic.v1"
    assert "p0_cause_counts" in out
    assert set(out["p0_cause_counts"].keys()) == {
        "calibration_not_computable", "calibration_fail", "promotion_gate_blocked", "sample_size_under_min",
        "input_not_computable_spike", "proof_p0_link", "operator_queue_policy", "replay_variation_edge", "not_computable"
    }
    assert out["safety_flags"] == {"execution_triggered": False, "runtime_mutation": False, "authority_leak_detected": False}


def test_calibration_fail_detection(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt(cal_status="FAIL", gate="FAIL"))
    out = diag.run_p0_root_cause_diagnostic(str(seed), cycles=4)
    assert out["p0_cause_counts"]["calibration_fail"] == 4
    assert out["dominant_p0_cause"] == "CALIBRATION_FAIL"


def test_sample_size_under_min_detection(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt(sample=2, p0=1))
    out = diag.run_p0_root_cause_diagnostic(str(seed), cycles=4)
    assert out["p0_cause_counts"]["sample_size_under_min"] == 4


def test_operator_queue_policy_detection(tmp_path: Path, monkeypatch):
    seed = _write_payload(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(diag, "run_replay_cycle", lambda *_args, **_kwargs: _receipt(cal_status="PASS", gate="PASS", p0=1))
    out = diag.run_p0_root_cause_diagnostic(str(seed), cycles=4)
    assert out["p0_cause_counts"]["operator_queue_policy"] == 4
