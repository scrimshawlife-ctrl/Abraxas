import json
import subprocess
import sys
from pathlib import Path


def test_run_mbom_v1_returns_not_computable_for_unregistered_subsystem(tmp_path: Path):
    request = tmp_path / "mbom_request.json"
    request.write_text(
        json.dumps(
            {
                "request_id": "MBOM-REQ-REG-0001",
                "lifecycle_states": {"a": "STABLE"},
                "domain_signals": [],
                "resonance_score": 0.0,
            }
        ),
        encoding="utf-8",
    )

    expected = tmp_path / "expected_subsystems.json"
    expected.write_text(json.dumps({"version": 1, "subsystems": ["oracle_signal_layer_v2"]}), encoding="utf-8")

    cp = subprocess.run(
        [
            sys.executable,
            "scripts/run_mbom_v1.py",
            "--request",
            str(request),
            "--expected-subsystems",
            str(expected),
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 2
    payload = json.loads(cp.stdout)
    assert payload["status"] == "NOT_COMPUTABLE"
    assert payload["reason"] == "subsystem_not_registered_in_expected_subsystems"
    assert payload["artifacts"] == {}


def test_run_mbom_v1_returns_not_computable_for_invalid_expected_subsystems_file(tmp_path: Path):
    request = tmp_path / "mbom_request.json"
    request.write_text(
        json.dumps(
            {
                "request_id": "MBOM-REQ-REG-0002",
                "lifecycle_states": {"a": "STABLE"},
                "domain_signals": [],
                "resonance_score": 0.0,
            }
        ),
        encoding="utf-8",
    )

    expected = tmp_path / "expected_subsystems.json"
    expected.write_text("{not-json", encoding="utf-8")

    cp = subprocess.run(
        [
            sys.executable,
            "scripts/run_mbom_v1.py",
            "--request",
            str(request),
            "--expected-subsystems",
            str(expected),
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 2
    payload = json.loads(cp.stdout)
    assert payload["status"] == "NOT_COMPUTABLE"
    assert payload["reason"] == "expected_subsystems_unreadable_or_invalid"
    assert payload["artifacts"] == {}
