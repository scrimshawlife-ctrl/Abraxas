import json
import subprocess
import sys
from pathlib import Path


def test_validate_run_emits_validator_artifact(tmp_path: Path):
    out = tmp_path / "validator.json"
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/validate_run.py",
            "--run-id",
            "RUN-1",
            "--artifact-id",
            "ART-1",
            "--ledger-record-id",
            "REC-1",
            "--packet-id",
            "PKT-1",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0
    data = json.loads(out.read_text())
    assert data["status"] == "VALIDATOR-VISIBLE"
