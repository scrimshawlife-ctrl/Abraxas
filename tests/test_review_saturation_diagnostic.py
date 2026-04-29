import json
from pathlib import Path

from scripts.run_review_saturation_diagnostic import run_review_saturation_diagnostic


def _write_payload(tmp_path: Path) -> Path:
    payload = {
        "schema_version": "ABXReplayInput.v1",
        "records": [
            {"record_id": "r1", "domain": "market_pse", "forecast_probability": 0.8, "outcome": "YES"},
            {"record_id": "r2", "domain": "market_pse", "forecast_probability": 0.3, "outcome": "NO"},
            {"record_id": "r3", "domain": "oracle", "forecast_probability": 0.7, "outcome": "YES"},
            {"record_id": "r4", "domain": "coding", "forecast_probability": 0.6, "outcome": "PENDING"},
            {"record_id": "r5", "domain": "memetic", "forecast_probability": 0.5, "outcome": "NOT_COMPUTABLE"},
        ],
    }
    p = tmp_path / "seed.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_review_diagnostic_deterministic(tmp_path: Path):
    seed = _write_payload(tmp_path)
    a = run_review_saturation_diagnostic(str(seed), cycles=10)
    b = run_review_saturation_diagnostic(str(seed), cycles=10)
    assert a == b


def test_review_diagnostic_shape_and_safety(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_review_saturation_diagnostic(str(seed), cycles=10)
    assert out["schema_version"] == "ABXReviewSaturationDiagnostic.v1"
    assert out["cycle_count"] == 10
    assert set(out["summary"].keys()) == {"pass_count", "review_required_count", "blocked_count", "avg_brier", "avg_confidence", "max_p0", "dominance_max"}
    assert set(out["cycle_cause_counts"].keys()) == {"low_confidence", "dominance_drift", "p1_review_items", "proof_hash_block", "not_computable_proof", "other"}
    assert out["safety_flags"] == {"execution_triggered": False, "runtime_mutation": False, "authority_leak_detected": False}


def test_pass_logic_too_strict_possible(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_review_saturation_diagnostic(str(seed), cycles=30)
    if (
        out["summary"]["pass_count"] == 0
        and out["summary"]["blocked_count"] == 0
        and out["summary"]["max_p0"] == 0
        and out["summary"]["avg_brier"] < 0.1
    ):
        assert out["dominant_review_driver"] in {"PASS_LOGIC_TOO_STRICT", "PROOF_HASH_BLOCK", "P1_REVIEW_ITEM_PERSISTENCE", "CONFIDENCE_THRESHOLD", "DOMINANCE_DRIFT", "NOT_COMPUTABLE"}
