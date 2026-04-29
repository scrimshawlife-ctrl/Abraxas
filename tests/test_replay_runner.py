import json
from pathlib import Path

from scripts.run_replay_cycle import run_replay_cycle


def _write_payload(tmp_path: Path, payload: dict) -> Path:
    p = tmp_path / "input.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_replay_runner_counts_and_flags(tmp_path: Path):
    payload = {
        "schema_version": "ABXReplayInput.v1",
        "records": [
            {"probability": 0.9, "outcome": "YES"},
            {"probability": 0.1, "outcome": "NO"},
            {"probability": 0.7, "outcome": "PENDING"},
            {"probability": 0.2, "outcome": "NO"},
        ],
    }
    receipt = run_replay_cycle(str(_write_payload(tmp_path, payload)))
    assert receipt["schema_version"] == "ABXReplayRunReceipt.v1"
    assert receipt["input_record_count"] == 4
    assert receipt["resolved_count"] == 3
    assert receipt["pending_count"] == 1
    assert receipt["execution_triggered"] is False
    assert receipt["runtime_mutation"] is False
    assert receipt["authority_leak_detected"] is False


def test_replay_runner_cycle_status_mapping(tmp_path: Path):
    blocked_payload = {
        "schema_version": "ABXReplayInput.v1",
        "records": [
            {"probability": 0.8, "outcome": "YES"},
            {"probability": 0.3, "outcome": "NO"},
        ],
    }
    blocked = run_replay_cycle(str(_write_payload(tmp_path, blocked_payload)))
    assert blocked["cycle_status"] == "BLOCKED"


def test_replay_runner_not_computable_handling(tmp_path: Path):
    payload = {
        "schema_version": "ABXReplayInput.v1",
        "records": [
            {"probability": 0.8, "outcome": "PENDING"},
            {"probability": None, "outcome": "YES"},
        ],
    }
    receipt = run_replay_cycle(str(_write_payload(tmp_path, payload)))
    assert receipt["cycle_status"] == "NOT_COMPUTABLE"
    assert receipt["resolved_count"] == 0


def _strip_time_fields(value):
    if isinstance(value, dict):
        return {k: _strip_time_fields(v) for k, v in value.items() if k not in {"run_id", "created_at", "generated_at"}}
    if isinstance(value, list):
        return [_strip_time_fields(v) for v in value]
    return value


def test_replay_runner_deterministic_surface_excluding_time(tmp_path: Path):
    payload = {
        "schema_version": "ABXReplayInput.v1",
        "records": [
            {"probability": 0.9, "outcome": "YES"},
            {"probability": 0.1, "outcome": "NO"},
            {"probability": 0.2, "outcome": "NO"},
        ],
    }
    path = _write_payload(tmp_path, payload)
    a = run_replay_cycle(str(path))
    b = run_replay_cycle(str(path))

    assert _strip_time_fields(a) == _strip_time_fields(b)


def test_replay_runner_with_write_artifacts_binds_hashes(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = {
        "schema_version": "ABXReplayInput.v1",
        "records": [
            {"probability": 0.9, "outcome": "YES"},
            {"probability": 0.1, "outcome": "NO"},
            {"probability": 0.2, "outcome": "NO"},
        ],
    }
    receipt = run_replay_cycle(str(_write_payload(tmp_path, payload)), write_artifacts=True)

    for item in receipt["proof_state_set"]["items"]:
        assert item["source_artifact_sha256"].startswith("sha256:")
        assert item["source_artifact_sha256"] != "NOT_COMPUTABLE"

    run_dir = Path("out/replay/artifacts") / receipt["run_id"]
    assert (run_dir / "calibration.json").exists()
    assert (run_dir / "advisory.json").exists()
    assert (run_dir / "fusion.json").exists()
    assert (run_dir / "operator_queue.json").exists()


def test_replay_runner_without_artifacts_remains_fail_closed(tmp_path: Path):
    payload = {
        "schema_version": "ABXReplayInput.v1",
        "records": [
            {"probability": 0.9, "outcome": "YES"},
            {"probability": 0.1, "outcome": "NO"},
            {"probability": 0.2, "outcome": "NO"},
        ],
    }
    receipt = run_replay_cycle(str(_write_payload(tmp_path, payload)))
    statuses = {item["display_status"] for item in receipt["proof_state_set"]["items"]}
    hashes = {item["source_artifact_sha256"] for item in receipt["proof_state_set"]["items"]}
    assert "NOT_COMPUTABLE" in statuses
    assert hashes == {"NOT_COMPUTABLE"}
