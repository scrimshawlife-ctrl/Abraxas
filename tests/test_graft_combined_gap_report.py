from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock


def _fake_subprocess_run(args, **kwargs):
    """Fake subprocess.run that writes pre-populated reports when called."""
    # Both sub-scripts are no-ops in test — we pre-populate the files instead.
    return MagicMock(returncode=0)


def test_combined_report_produces_valid_artifact(tmp_path, monkeypatch):
    """GraftCombinedGapReport.v1 artifact must exist with both sub-reports after run."""
    # Pre-populate sub-reports the combiner reads
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

    # Change cwd so the script's relative paths resolve inside tmp_path
    monkeypatch.chdir(tmp_path)

    from scripts.graft_combined_gap_report import main

    with patch("scripts.graft_combined_gap_report.subprocess.run", side_effect=_fake_subprocess_run):
        main()

    combined = reports_dir / "graft_combined_gap_report.latest.json"
    assert combined.exists(), f"Expected {combined} to exist"

    report = json.loads(combined.read_text())
    assert report["schema_version"] == "GraftCombinedGap.v1"
    assert "generated_at" in report
    assert "analyzer_report" in report
    assert "todo_report" in report
    assert report["analyzer_report"]["modes"]["binding"]["total_hits"] == 8
    assert report["todo_report"]["totals"]["todo"] == 57