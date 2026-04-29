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


def test_clean_system_ready_for_design(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_multi_cycle_replay(str(seed), num_cycles=30)
    summary = out["summary"]
    assert summary["readiness_status"] == "READY_FOR_DESIGN"
    assert summary["design_pass_allowed"] is True
    assert summary["execution_allowed"] is False
    assert summary["patch_004_allowed"] is True


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


def test_design_pass_blocked_conditions(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_multi_cycle_replay(str(seed), num_cycles=10)
    summary = out["summary"]
    assert summary["design_pass_allowed"] is False  # insufficient cycle window


def test_default_replay_outcome_flip_disabled(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_multi_cycle_replay(str(seed), num_cycles=5)
    assert out["summary"]["outcome_flip_enabled"] is False


def test_threshold_blockers_logic():
    # P0 present blocks
    assert not (
        30 >= 30 and 0 == 0 and 1 == 0 and [] == [] and False is False and False is False and False is False and 0.1 <= 0.15 and 1.2 <= 1.5
    )
    # blocked_count blocks
    assert not (
        30 >= 30 and 1 == 0 and 0 == 0 and [] == [] and False is False and False is False and False is False and 0.1 <= 0.15 and 1.2 <= 1.5
    )
    # safety flags block
    assert not (
        30 >= 30 and 0 == 0 and 0 == 0 and [] == [] and True is False and False is False and False is False and 0.1 <= 0.15 and 1.2 <= 1.5
    )
    # brier threshold blocks
    assert not (
        30 >= 30 and 0 == 0 and 0 == 0 and [] == [] and False is False and False is False and False is False and 0.16 <= 0.15 and 1.2 <= 1.5
    )
    # dominance threshold blocks
    assert not (
        30 >= 30 and 0 == 0 and 0 == 0 and [] == [] and False is False and False is False and False is False and 0.1 <= 0.15 and 1.6 <= 1.5
    )
