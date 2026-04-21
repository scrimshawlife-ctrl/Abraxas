from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.sync_invariance_to_notion import map_row_to_notion_properties


def test_promote_sanitizes_to_hold() -> None:
    row = {"Name": "Row A", "Promotion Recommendation": "PROMOTE"}
    properties = map_row_to_notion_properties(row)
    assert properties["Promotion Recommendation"]["select"]["name"] == "HOLD"


def test_payload_maps_required_properties() -> None:
    row = {
        "Name": "Invariance Row",
        "Run ID": "RUN-GAP-FIRST-0001",
        "Artifact Type": "closure_validation_report",
        "Artifact Path": "artifacts_seal/runs/RUN-GAP-FIRST-0001/closure_validation_report.json",
        "Artifact Hash": "abc123",
        "Execution Mode": "sandbox",
        "Workspace Scope": "workspace-only",
        "Determinism Pair Status": "PASS",
        "Invariance State": "PASS",
        "Drift Severity": "LOW",
        "Repair Loop Reopened": False,
        "Validator Status": "PASS",
        "Promotion Recommendation": "HOLD",
        "Notes": "deterministic",
        "Execution Date": "2026-04-21",
    }
    properties = map_row_to_notion_properties(row)
    assert properties["Name"]["title"][0]["text"]["content"] == "Invariance Row"
    assert properties["Run ID"]["rich_text"][0]["text"]["content"] == "RUN-GAP-FIRST-0001"
    assert properties["Artifact Type"]["select"]["name"] == "closure_validation_report"
    assert properties["Execution Date"]["date"]["start"] == "2026-04-21"
    assert properties["Repair Loop Reopened"]["checkbox"] is False


def test_dry_run_does_not_require_token(tmp_path: Path) -> None:
    run_id = "RUN-GAP-FIRST-0001"
    input_path = tmp_path / f"{run_id}.abx_invariance_tracker_rows.json"
    output_path = tmp_path / f"{run_id}.notion_sync_report.json"
    input_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "Name": "Row A",
                        "Run ID": run_id,
                        "Promotion Recommendation": "PROMOTE",
                    }
                ]
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    env = dict(os.environ)
    env.pop("NOTION_TOKEN", None)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/sync_invariance_to_notion.py",
            "--run-id",
            run_id,
            "--input",
            input_path.as_posix(),
            "--output",
            output_path.as_posix(),
            "--dry-run",
        ],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["mapped_payloads"][0]["Promotion Recommendation"]["select"]["name"] == "HOLD"


def test_missing_report_file_fails_clearly(tmp_path: Path) -> None:
    run_id = "RUN-GAP-FIRST-0001"
    missing_input = tmp_path / "missing.json"
    output_path = tmp_path / "out.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/sync_invariance_to_notion.py",
            "--run-id",
            run_id,
            "--input",
            missing_input.as_posix(),
            "--output",
            output_path.as_posix(),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "input report not found" in result.stdout
