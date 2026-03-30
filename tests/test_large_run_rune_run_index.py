from __future__ import annotations

import json
from pathlib import Path

from scripts.run_large_run_rune_run_index import build_rune_run_index


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_rune_run_index_groups_runs_by_rune_id(tmp_path: Path) -> None:
    _write(
        tmp_path / "out" / "validators" / "execution-validation-RUN-X.json",
        {
            "runId": "RUN-X",
            "status": "VALID",
            "runeContext": {"runeIds": ["RUNE.DIFF", "RUNE.INGEST"], "phases": ["VALIDATE"]},
        },
    )
    _write(
        tmp_path / "out" / "operator" / "operator-projection-RUN-X.json",
        {"run_id": "RUN-X", "proof_closure_status": "COMPLETE"},
    )

    artifact = build_rune_run_index(
        base_dir=tmp_path,
        batch_id="BATCH-INDEX-001",
        timestamp="2026-03-30T00:00:00+00:00",
    )

    assert artifact["status"] == "SUCCESS"
    assert artifact["outputs"]["validator_run_count"] == 1
    assert artifact["outputs"]["rune_count"] == 2
    rune_ids = [entry["rune_id"] for entry in artifact["outputs"]["runes"]]
    assert rune_ids == ["RUNE.DIFF", "RUNE.INGEST"]


def test_rune_run_index_marks_not_computable_without_rune_context(tmp_path: Path) -> None:
    _write(
        tmp_path / "out" / "validators" / "execution-validation-RUN-Y.json",
        {"runId": "RUN-Y", "status": "VALID", "runeContext": {"runeIds": [], "phases": []}},
    )

    artifact = build_rune_run_index(
        base_dir=tmp_path,
        batch_id="BATCH-INDEX-002",
        timestamp="2026-03-30T00:00:00+00:00",
    )

    assert artifact["status"] == "NOT_COMPUTABLE"
    assert artifact["outputs"]["validator_run_count"] == 1
    assert artifact["outputs"]["rune_count"] == 0


def test_rune_run_index_is_deterministic(tmp_path: Path) -> None:
    _write(
        tmp_path / "out" / "validators" / "execution-validation-RUN-Z.json",
        {
            "runId": "RUN-Z",
            "status": "VALID",
            "runeContext": {"runeIds": ["RUNE.DIFF"], "phases": ["AUDIT"]},
        },
    )
    _write(
        tmp_path / "out" / "operator" / "operator-projection-RUN-Z.json",
        {"run_id": "RUN-Z", "proof_closure_status": "COMPLETE"},
    )

    a = build_rune_run_index(
        base_dir=tmp_path,
        batch_id="BATCH-INDEX-003",
        timestamp="2026-03-30T00:00:00+00:00",
    )
    b = build_rune_run_index(
        base_dir=tmp_path,
        batch_id="BATCH-INDEX-003",
        timestamp="2026-03-30T00:00:00+00:00",
    )

    assert a == b
