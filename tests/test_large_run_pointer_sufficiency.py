from __future__ import annotations

import json
from pathlib import Path

from scripts.run_large_run_pointer_sufficiency import build_pointer_sufficiency_report


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_pointer_sufficiency_success_when_all_runs_meet_threshold(tmp_path: Path) -> None:
    _write(
        tmp_path / "out" / "validators" / "execution-validation-RUN-A.json",
        {
            "runId": "RUN-A",
            "artifactId": "execution-validation-RUN-A",
            "correlation": {"pointers": ["a", "b"]},
        },
    )
    _write(
        tmp_path / "out" / "validators" / "execution-validation-RUN-B.json",
        {
            "runId": "RUN-B",
            "artifactId": "execution-validation-RUN-B",
            "correlation": {"pointers": ["x"]},
        },
    )

    report = build_pointer_sufficiency_report(
        base_dir=tmp_path,
        batch_id="BATCH-PTR-001",
        timestamp="2026-03-30T00:00:00+00:00",
        min_pointers=1,
    )

    assert report["status"] == "SUCCESS"
    assert report["outputs"]["run_count"] == 2
    assert report["outputs"]["sufficient_count"] == 2
    assert report["outputs"]["not_computable_count"] == 0


def test_pointer_sufficiency_not_computable_with_missing_pointers(tmp_path: Path) -> None:
    _write(
        tmp_path / "out" / "validators" / "execution-validation-RUN-C.json",
        {
            "runId": "RUN-C",
            "artifactId": "execution-validation-RUN-C",
            "correlation": {"pointers": []},
        },
    )

    report = build_pointer_sufficiency_report(
        base_dir=tmp_path,
        batch_id="BATCH-PTR-002",
        timestamp="2026-03-30T00:00:00+00:00",
        min_pointers=1,
    )

    assert report["status"] == "NOT_COMPUTABLE"
    assert report["outputs"]["run_count"] == 1
    assert report["outputs"]["not_computable_count"] == 1
    row = report["outputs"]["runs"][0]
    assert row["sufficiency_state"] == "NOT_COMPUTABLE"
    assert "pointer-count-below-threshold:0<1" in row["reason_codes"]


def test_pointer_sufficiency_report_is_deterministic(tmp_path: Path) -> None:
    _write(
        tmp_path / "out" / "validators" / "execution-validation-RUN-D.json",
        {
            "runId": "RUN-D",
            "artifactId": "execution-validation-RUN-D",
            "correlation": {"pointers": ["p1"]},
        },
    )

    a = build_pointer_sufficiency_report(
        base_dir=tmp_path,
        batch_id="BATCH-PTR-003",
        timestamp="2026-03-30T00:00:00+00:00",
        min_pointers=1,
    )
    b = build_pointer_sufficiency_report(
        base_dir=tmp_path,
        batch_id="BATCH-PTR-003",
        timestamp="2026-03-30T00:00:00+00:00",
        min_pointers=1,
    )
    assert a == b
