from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock


def _fake_subprocess_run(args, **kwargs):
    """Fake subprocess.run that writes pre-populated reports when called."""
    return MagicMock(returncode=0)


def _fake_subprocess_check_output(args, **kwargs):
    """Fake subprocess.check_output for graft ask."""
    return "graft: no hits in test"


def test_combined_report_produces_valid_artifact(tmp_path, monkeypatch):
    """GraftCombinedGapReport.v1 artifact must exist with sub-reports + preflight after run."""
    reports_dir = tmp_path / "out" / "reports"
    reports_dir.mkdir(parents=True)

    analyzer_data = {
        "schema_version": "GraftGapReport.v1",
        "modes": {
            "binding": {"total_hits": 8, "top_symbols": []},
            "residual": {"total_hits": 8, "top_symbols": []},
        },
    }
    todo_data = {
        "schema": "TodoMarkerScan.v0",
        "totals": {"files_with_markers": 17, "todo": 57, "fixme": 5},
    }

    (reports_dir / "graft_gap_report.latest.json").write_text(json.dumps(analyzer_data))
    (reports_dir / "todo_markers.latest.json").write_text(json.dumps(todo_data))

    monkeypatch.chdir(tmp_path)

    from scripts.graft_combined_gap_report import main

    with patch("scripts.graft_combined_gap_report.subprocess.run", side_effect=_fake_subprocess_run), \
         patch("scripts.graft_combined_gap_report.subprocess.check_output", side_effect=_fake_subprocess_check_output):
        main()

    combined = reports_dir / "graft_combined_gap_report.latest.json"
    assert combined.exists(), f"Expected {combined} to exist"

    report = json.loads(combined.read_text())
    assert report["schema_version"] == "GraftCombinedGap.v1"
    assert "generated_at" in report
    assert "analyzer_report" in report
    assert "todo_report" in report
    assert "promotion_preflight" in report
    assert "graft_promotion_hits" in report
    assert report["analyzer_report"]["modes"]["binding"]["total_hits"] == 8
    assert report["todo_report"]["totals"]["todo"] == 57


def test_combined_report_includes_promotion_preflight(tmp_path, monkeypatch):
    """GraftCombinedGap.v1 must include promotion_preflight after wire-in."""
    reports_dir = tmp_path / "out" / "reports"
    reports_dir.mkdir(parents=True)

    analyzer_data = {
        "schema_version": "GraftGapReport.v1",
        "modes": {
            "binding": {"total_hits": 1, "top_symbols": []},
            "residual": {"total_hits": 1, "top_symbols": []},
        },
    }
    todo_data = {
        "schema": "TodoMarkerScan.v0",
        "totals": {"files_with_markers": 1, "todo": 1, "fixme": 0},
    }
    preflight_data = {
        "advisory_id": "test-id",
        "advisory_state": "READY_CANDIDATE",
        "blockers": [],
        "timestamp_utc": "2026-01-01T00:00:00Z",
    }

    (reports_dir / "graft_gap_report.latest.json").write_text(json.dumps(analyzer_data))
    (reports_dir / "todo_markers.latest.json").write_text(json.dumps(todo_data))
    (reports_dir / "promotion_preflight.latest.json").write_text(json.dumps(preflight_data))

    monkeypatch.chdir(tmp_path)

    from scripts.graft_combined_gap_report import main

    with patch("scripts.graft_combined_gap_report.subprocess.run", side_effect=_fake_subprocess_run), \
         patch("scripts.graft_combined_gap_report.subprocess.check_output", side_effect=_fake_subprocess_check_output):
        main()

    combined = reports_dir / "graft_combined_gap_report.latest.json"
    assert combined.exists()

    report = json.loads(combined.read_text())
    assert "promotion_preflight" in report, (
        "combined report must include promotion_preflight after wire-in"
    )
    assert report["promotion_preflight"]["advisory_state"] == "READY_CANDIDATE"
    assert report["promotion_preflight"]["advisory_id"] == "test-id"