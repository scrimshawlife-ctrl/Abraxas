from __future__ import annotations

import json
from pathlib import Path

from abx.gap_closure_invariance import (
    project_gap_closure_invariance,
    read_gap_closure_invariance_payload,
)


def _sample_raw() -> dict:
    return {
        "run_id": "RUN-GAP-FIRST-0001",
        "status": "PASS",
        "readiness_state": "partial",
        "promotion_recommendation": "HOLD",
        "invariance_counts": {
            "UNCHECKED": 1,
            "PROVISIONAL": 2,
            "STABLE": 3,
        },
        "required_thresholds": {"min_provisional_or_stable_rows": 3},
        "unmet_conditions": ["z-gap", "a-gap"],
    }


def test_gap_closure_invariance_projection_schema_and_ordering() -> None:
    projection = project_gap_closure_invariance(_sample_raw())
    assert projection["run_id"] == "RUN-GAP-FIRST-0001"
    assert projection["invariance_counts"] == {
        "total": 6,
        "unchecked": 1,
        "provisional": 2,
        "stable": 3,
    }
    assert projection["unmet_conditions"] == ["a-gap", "z-gap"]


def test_gap_closure_invariance_missing_artifact_not_computable(tmp_path: Path) -> None:
    payload = read_gap_closure_invariance_payload(tmp_path / "missing.json")
    assert payload["status"] == "NOT_COMPUTABLE"
    assert payload["raw"] is None
    assert payload["projection"]["readiness_state"] == "NOT_COMPUTABLE"


def test_gap_closure_invariance_read_payload_projects(tmp_path: Path) -> None:
    path = tmp_path / "gap_closure_stabilization_report.json"
    path.write_text(json.dumps(_sample_raw()), encoding="utf-8")
    payload = read_gap_closure_invariance_payload(path)
    assert payload["status"] == "PASS"
    assert payload["reason"] == "ok"
    assert payload["projection"]["promotion_decision"] == "HOLD"
