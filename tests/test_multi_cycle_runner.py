import json
from pathlib import Path

from scripts.run_multi_cycle_replay import _classify_stability, run_multi_cycle_replay


def _write_payload(tmp_path: Path) -> Path:
    payload = {
        "schema_version": "ABXReplayInput.v1",
        "records": [
            {"record_id": "r1", "domain": "market_pse", "forecast_probability": 0.8, "outcome": "YES"},
            {"record_id": "r2", "domain": "market_pse", "forecast_probability": 0.3, "outcome": "NO"},
            {"record_id": "r3", "domain": "oracle", "forecast_probability": 0.7, "outcome": "YES"},
            {"record_id": "r4", "domain": "coding", "forecast_probability": 0.6, "outcome": "PENDING"},
        ],
    }
    p = tmp_path / "seed.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_multi_cycle_deterministic_summary(tmp_path: Path):
    seed = _write_payload(tmp_path)
    a = run_multi_cycle_replay(str(seed), num_cycles=5)
    b = run_multi_cycle_replay(str(seed), num_cycles=5)
    assert a["summary"] == b["summary"]


def test_multi_cycle_aggregation_and_safety_flags(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_multi_cycle_replay(str(seed), num_cycles=6)
    assert out["summary"]["cycle_count"] == 6
    assert len(out["cycles"]) == 6
    assert all(row["execution_triggered"] is False for row in out["cycles"])
    assert all(row["runtime_mutation"] is False for row in out["cycles"])
    assert all(row["authority_leak_detected"] is False for row in out["cycles"])


def test_multi_cycle_small_dataset_safe(tmp_path: Path):
    payload = {"schema_version": "ABXReplayInput.v1", "records": [{"forecast_probability": 0.9, "outcome": "YES"}]}
    p = tmp_path / "small.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    out = run_multi_cycle_replay(str(p), num_cycles=2)
    assert out["summary"]["cycle_count"] == 2
    assert out["summary"]["stability_status"] in {"BLOCKED", "UNSTABLE", "STABLE", "REVIEW_REQUIRED", "HARD_BLOCKED", "LOW_CONFIDENCE_REVIEW", "NOT_COMPUTABLE"}


def test_multi_cycle_confidence_not_optimistic(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_multi_cycle_replay(str(seed), num_cycles=10)
    assert out["summary"]["avg_confidence"] < 0.74


def test_classify_low_confidence_review():
    metrics = {"cycle_count": 10, "blocked_count": 6, "avg_brier": 0.1664, "avg_confidence": 0.15, "max_p0": 1, "dominance_max": 1.4}
    cycles = [{"p0_count": 1}, {"p0_count": 0}, {"p0_count": 1}, {"p0_count": 0}]
    status, hard, flags = _classify_stability(metrics, cycles)
    assert status == "LOW_CONFIDENCE_REVIEW"
    assert hard == []
    assert "LOW_CONFIDENCE" in flags


def test_classify_hard_blocked_on_safety_flag():
    metrics = {"cycle_count": 5, "blocked_count": 0, "avg_brier": 0.1, "avg_confidence": 0.7, "max_p0": 0, "dominance_max": 1.0, "execution_triggered": True}
    status, hard, _ = _classify_stability(metrics, [{"p0_count": 0}])
    assert status == "HARD_BLOCKED"
    assert "EXECUTION_TRIGGERED" in hard


def test_classify_hard_blocked_on_consecutive_p0():
    metrics = {"cycle_count": 5, "blocked_count": 1, "avg_brier": 0.2, "avg_confidence": 0.7, "max_p0": 1, "dominance_max": 1.2}
    cycles = [{"p0_count": 1}, {"p0_count": 1}, {"p0_count": 1}, {"p0_count": 0}]
    status, hard, _ = _classify_stability(metrics, cycles)
    assert status == "HARD_BLOCKED"
    assert "PERSISTENT_P0" in hard


def test_classify_intermittent_p0_not_hard_blocked():
    metrics = {"cycle_count": 6, "blocked_count": 2, "avg_brier": 0.16, "avg_confidence": 0.34, "max_p0": 1, "dominance_max": 1.4}
    cycles = [{"p0_count": 1}, {"p0_count": 0}, {"p0_count": 1}, {"p0_count": 0}]
    status, hard, _ = _classify_stability(metrics, cycles)
    assert status != "HARD_BLOCKED"
    assert hard == []


def test_evidence_window_insufficient(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_multi_cycle_replay(str(seed), num_cycles=10)
    assert out["summary"]["cycle_count_observed"] == 10
    assert out["summary"]["cycle_count_required"] == 30
    assert out["summary"]["evidence_window_status"] == "INSUFFICIENT"
    assert out["summary"]["patch_004_allowed"] is False


def test_evidence_window_sufficient(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_multi_cycle_replay(str(seed), num_cycles=30)
    assert out["summary"]["cycle_count_observed"] == 30
    assert out["summary"]["evidence_window_status"] == "SUFFICIENT"


def test_patch_004_allowed_only_ready_and_sufficient():
    cycles = [{"p0_count": 0}] * 30
    metrics = {
        "cycle_count": 30,
        "blocked_count": 0,
        "avg_brier": 0.1,
        "avg_confidence": 0.6,
        "max_p0": 0,
        "dominance_max": 1.2,
        "review_required_count": 0,
    }
    status, hard, flags = _classify_stability(metrics, cycles)
    assert status == "STABLE"
    readiness = "READY" if status == "STABLE" else status
    patch_004_allowed = True if (30 >= 30 and readiness == "READY") else False
    assert patch_004_allowed is True


def test_default_replay_outcome_flip_disabled(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_multi_cycle_replay(str(seed), num_cycles=5)
    assert out["summary"]["outcome_flip_enabled"] is False
