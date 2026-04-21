import json
import subprocess
import sys
from pathlib import Path


def _base_release_manifest() -> dict:
    return {
        "record_type": "release_manifest",
        "timestamp": "2026-01-01T00:00:00Z",
        "status": "SUCCESS",
        "provenance": {},
        "correlation_pointers": ["out/proof_runs/RUN-1/runtime_artifact.json"],
        "correlation_pointer_state": "present",
        "correlation_pointer_unresolved_reasons": [],
        "registration_receipt": {
            "label": "subsystem_registration_check",
            "status": "PASS",
        },
    }


def test_release_manifest_requires_registration_receipt(tmp_path: Path):
    record = tmp_path / "release.json"
    payload = _base_release_manifest()
    payload.pop("registration_receipt")
    record.write_text(json.dumps(payload), encoding="utf-8")

    cp = subprocess.run(
        [
            sys.executable,
            ".abraxas/scripts/validate_governance_record.py",
            "--record",
            str(record),
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 1


def test_release_manifest_accepts_valid_registration_receipt(tmp_path: Path):
    record = tmp_path / "release.json"
    record.write_text(json.dumps(_base_release_manifest()), encoding="utf-8")

    cp = subprocess.run(
        [
            sys.executable,
            ".abraxas/scripts/validate_governance_record.py",
            "--record",
            str(record),
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0


def test_release_manifest_accepts_unresolved_pointer_state(tmp_path: Path):
    record = tmp_path / "release.json"
    payload = _base_release_manifest()
    payload["correlation_pointers"] = []
    payload["correlation_pointer_state"] = "unresolved"
    payload["correlation_pointer_unresolved_reasons"] = ["artifact_missing:out/proof_runs/RUN-1/runtime_artifact.json"]
    record.write_text(json.dumps(payload), encoding="utf-8")

    cp = subprocess.run(
        [
            sys.executable,
            ".abraxas/scripts/validate_governance_record.py",
            "--record",
            str(record),
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0
