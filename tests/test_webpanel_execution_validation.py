from __future__ import annotations

import json
from pathlib import Path

from webpanel.execution_validation import load_execution_validation_for_run


def test_load_execution_validation_exact_path(tmp_path: Path):
    validators_dir = tmp_path / "out" / "validators"
    validators_dir.mkdir(parents=True, exist_ok=True)
    payload = {"runId": "RUN-1", "status": "VALID", "artifactId": "execution-validation-RUN-1"}
    path = validators_dir / "execution-validation-RUN-1.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_execution_validation_for_run("RUN-1", validators_dir=validators_dir)
    assert loaded is not None
    assert loaded["runId"] == "RUN-1"
    assert loaded["status"] == "VALID"
    assert loaded["_source_path"].endswith("execution-validation-RUN-1.json")


def test_load_execution_validation_scans_by_run_id(tmp_path: Path):
    validators_dir = tmp_path / "out" / "validators"
    validators_dir.mkdir(parents=True, exist_ok=True)

    (validators_dir / "x.json").write_text(json.dumps({"runId": "RUN-A", "status": "ERROR"}), encoding="utf-8")
    (validators_dir / "y.json").write_text(json.dumps({"runId": "RUN-B", "status": "VALID"}), encoding="utf-8")

    loaded = load_execution_validation_for_run("RUN-B", validators_dir=validators_dir)
    assert loaded is not None
    assert loaded["runId"] == "RUN-B"
    assert loaded["status"] == "VALID"
    assert loaded["_source_path"].endswith("y.json")

