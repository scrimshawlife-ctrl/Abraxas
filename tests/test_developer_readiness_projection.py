from __future__ import annotations

import json
from pathlib import Path

from abx.developer_readiness import project_developer_readiness, read_developer_readiness_payload


def _sample_report() -> dict:
    return {
        "run_id": "DEV-READINESS-ABC123",
        "timestamp_utc": "2026-04-21T00:00:00Z",
        "status": "PARTIAL",
        "checks": [
            {
                "check_id": "b-check",
                "label": "B",
                "command": "pytest -q b",
                "status": "PASS",
                "return_code": 0,
                "missing_files": [],
            },
            {
                "check_id": "a-check",
                "label": "A",
                "command": "pytest -q a",
                "status": "NOT_PRESENT",
                "return_code": None,
                "missing_files": ["tests/a.py"],
            },
        ],
        "missing_surfaces": [{"check_id": "a-check", "missing_files": ["tests/a.py"]}],
        "recommended_next_actions": ["add a", "add a"],
        "provenance": {"script": "scripts/run_developer_readiness.py"},
    }


def test_projection_schema_and_deterministic_ordering() -> None:
    projected = project_developer_readiness(_sample_report())
    assert projected["status"] == "PARTIAL"
    assert [row["check_id"] for row in projected["checks"]] == ["a-check", "b-check"]
    assert projected["provenance"]["deterministic_ordering"] == ["a-check", "b-check"]


def test_missing_file_behavior_not_computable(tmp_path: Path) -> None:
    payload = read_developer_readiness_payload(tmp_path / "missing.json")
    assert payload["status"] == "NOT_COMPUTABLE"
    assert payload["raw"] is None
    assert payload["projection"]["status"] == "NOT_COMPUTABLE"


def test_read_payload_projects_raw_report(tmp_path: Path) -> None:
    report_path = tmp_path / "developer_readiness.json"
    report_path.write_text(json.dumps(_sample_report()), encoding="utf-8")
    payload = read_developer_readiness_payload(report_path)
    assert payload["status"] == "PARTIAL"
    assert payload["reason"] == "ok"
    assert payload["projection"]["run_id"] == "DEV-READINESS-ABC123"
