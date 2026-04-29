import json
from pathlib import Path

from scripts.run_replay_profile_diagnostics import PROFILE_IDS, run_profile_diagnostics


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


def test_profile_diagnostics_deterministic(tmp_path: Path):
    seed = _write_payload(tmp_path)
    a = run_profile_diagnostics(str(seed), cycles=10)
    b = run_profile_diagnostics(str(seed), cycles=10)
    assert a == b


def test_profile_diagnostics_profiles_and_schema(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_profile_diagnostics(str(seed), cycles=5)
    assert out["schema_version"] == "ABXReplayProfileDiagnostics.v1"
    assert out["cycles_per_profile"] == 5
    assert {p["profile_id"] for p in out["profiles"]} == set(PROFILE_IDS)
    assert set(out["safety_flags"].keys()) == {"execution_triggered", "runtime_mutation", "authority_leak_detected"}


def test_profile_diagnostics_safety_flags_false(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_profile_diagnostics(str(seed), cycles=6)
    assert out["safety_flags"]["execution_triggered"] is False
    assert out["safety_flags"]["runtime_mutation"] is False
    assert out["safety_flags"]["authority_leak_detected"] is False


def test_profile_diagnostics_known_driver(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_profile_diagnostics(str(seed), cycles=10)
    assert out["diagnosis"]["dominant_failure_driver"] in {"OUTCOME_FLIP", "SIGNAL_WEAKNESS", "NOT_COMPUTABLE"}


def test_profile_flip_flags(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_profile_diagnostics(str(seed), cycles=5)
    by_id = {p["profile_id"]: p["summary"] for p in out["profiles"]}
    assert by_id["BASELINE_CURRENT"]["outcome_flip_enabled"] is False
    assert by_id["NO_FLIP"]["outcome_flip_enabled"] is False
    assert by_id["LOW_DRIFT"]["outcome_flip_enabled"] is False
    assert by_id["HIGH_DRIFT"]["outcome_flip_enabled"] is False
    assert by_id["DOMAIN_ROTATION"]["outcome_flip_enabled"] is False
    assert by_id["FLIP_ONLY"]["outcome_flip_enabled"] is True


def test_flip_only_differs_from_baseline(tmp_path: Path):
    seed = _write_payload(tmp_path)
    out = run_profile_diagnostics(str(seed), cycles=10)
    by_id = {p["profile_id"]: p["summary"] for p in out["profiles"]}
    assert by_id["FLIP_ONLY"]["avg_brier"] != by_id["BASELINE_CURRENT"]["avg_brier"]
