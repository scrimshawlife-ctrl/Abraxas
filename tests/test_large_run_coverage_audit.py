from __future__ import annotations

import json
from pathlib import Path

from scripts.run_large_run_coverage_audit import build_large_run_coverage_artifact


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_large_run_coverage_audit_covers_run_with_both_surfaces(tmp_path: Path) -> None:
    run_id = "RUN-LARGE-0001"
    _write(
        tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json",
        {"runId": run_id, "status": "VALID", "artifactId": "execution-validation-RUN-LARGE-0001"},
    )
    _write(
        tmp_path / "out" / "operator" / f"operator-projection-{run_id}.json",
        {"run_id": run_id, "schema": "OperatorProjectionSummary.v1", "proof_closure_status": "COMPLETE"},
    )

    artifact, ledger_rows = build_large_run_coverage_artifact(
        base_dir=tmp_path,
        batch_id="BATCH-001",
        timestamp="2026-03-30T00:00:00+00:00",
    )

    assert artifact["status"] == "SUCCESS"
    assert artifact["outputs"]["run_count"] == 1
    assert artifact["outputs"]["covered_count"] == 1
    run_row = artifact["outputs"]["runs"][0]
    assert run_row["run_id"] == run_id
    assert run_row["coverage_state"] == "COVERED"
    assert run_row["reason_codes"] == []
    assert ledger_rows[0]["status"] == "COVERED"


def test_large_run_coverage_audit_marks_missing_projection_not_computable(tmp_path: Path) -> None:
    run_id = "RUN-LARGE-0002"
    _write(
        tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json",
        {"runId": run_id, "status": "VALID", "artifactId": "execution-validation-RUN-LARGE-0002"},
    )

    artifact, ledger_rows = build_large_run_coverage_artifact(
        base_dir=tmp_path,
        batch_id="BATCH-002",
        timestamp="2026-03-30T00:00:00+00:00",
    )

    assert artifact["status"] == "NOT_COMPUTABLE"
    assert artifact["outputs"]["run_count"] == 1
    assert artifact["outputs"]["not_computable_count"] == 1
    run_row = artifact["outputs"]["runs"][0]
    assert run_row["coverage_state"] == "NOT_COMPUTABLE"
    assert "missing-operator-projection" in run_row["reason_codes"]
    assert ledger_rows[0]["status"] == "NOT_COMPUTABLE"


def test_large_run_coverage_audit_is_deterministic(tmp_path: Path) -> None:
    run_id = "RUN-LARGE-0003"
    _write(
        tmp_path / "out" / "validators" / f"execution-validation-{run_id}.json",
        {"runId": run_id, "status": "VALID", "artifactId": "execution-validation-RUN-LARGE-0003"},
    )
    _write(
        tmp_path / "out" / "operator" / f"operator-projection-{run_id}.json",
        {"run_id": run_id, "schema": "OperatorProjectionSummary.v1", "proof_closure_status": "COMPLETE"},
    )

    a_artifact, a_rows = build_large_run_coverage_artifact(
        base_dir=tmp_path,
        batch_id="BATCH-003",
        timestamp="2026-03-30T00:00:00+00:00",
    )
    b_artifact, b_rows = build_large_run_coverage_artifact(
        base_dir=tmp_path,
        batch_id="BATCH-003",
        timestamp="2026-03-30T00:00:00+00:00",
    )

    assert a_artifact == b_artifact
    assert a_rows == b_rows
