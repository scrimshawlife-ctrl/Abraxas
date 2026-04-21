from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def test_invariance_logger_provisional_on_second_pass(tmp_path: Path) -> None:
    run_id = "RUN-GAP-FIRST-0001"
    run_dir = tmp_path / "artifacts" / run_id
    _write(run_dir / "gap_closure_run.json", {"run_id": run_id})
    _write(run_dir / "live_run_projection.json", {"run_id": run_id, "authority_boundary": "projection cannot alter canon status"})
    _write(
        run_dir / "closure_validation_report.json",
        {"run_id": run_id, "status": "PASS", "promotion_decision": "HOLD"},
    )
    _write(tmp_path / "out" / "validators" / f"{run_id}.gap_closure.validator.json", {"status": "PASS"})
    ledger_path = tmp_path / "out" / "ledger" / "abx_invariance_tracker.jsonl"
    report_path = tmp_path / "out" / "reports" / f"{run_id}.abx_invariance_tracker_rows.json"

    base_cmd = [
        sys.executable,
        "scripts/log_gap_closure_invariance.py",
        "--run-id",
        run_id,
        "--mode",
        "sandbox",
        "--workspace-scope",
        "workspace_only",
        "--artifacts-dir",
        (tmp_path / "artifacts").as_posix(),
        "--ledger-path",
        ledger_path.as_posix(),
        "--report-path",
        report_path.as_posix(),
    ]
    result_1 = subprocess.run(base_cmd, check=False, capture_output=True, text=True)
    result_2 = subprocess.run(base_cmd, check=False, capture_output=True, text=True)
    assert result_1.returncode == 0
    assert result_2.returncode == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    states = {row["Invariance State"] for row in report["rows"]}
    assert states == {"PROVISIONAL"}
