from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def test_producer_ensures_provisional_rows(tmp_path: Path) -> None:
    """TDD: after producer runs, stabilization report has >= 3 PROVISIONAL/STABLE rows."""
    run_id = "RUN-PRODUCER-TDD-0001"
    run_dir = tmp_path / "artifacts_seal" / "runs" / run_id
    out_dir = tmp_path / "out"

    # Seed artifacts so log_gap_closure_invariance has real files to hash.
    _write(run_dir / "gap_closure_run.json", {"run_id": run_id, "mode": "sandbox"})
    _write(run_dir / "live_run_projection.json", {"run_id": run_id, "authority_boundary": "projection cannot alter canon status"})
    _write(run_dir / "closure_validation_report.json", {"run_id": run_id, "status": "PASS", "promotion_decision": "HOLD"})
    _write(out_dir / "validators" / f"{run_id}.gap_closure.validator.json", {"status": "PASS"})

    # Run the producer — it handles both logging invariance rows and stabilization report.
    result = subprocess.run(
        [
            sys.executable,
            "scripts/produce_minimal_invariance_rows.py",
            "--run-id", run_id,
            "--artifacts-dir", (tmp_path / "artifacts_seal" / "runs").as_posix(),
            "--report-dir", (out_dir / "reports").as_posix(),
            "--ledger-path", (out_dir / "ledger" / "abx_invariance_tracker.jsonl").as_posix(),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"producer failed (exit {result.returncode}): stderr={result.stderr}"

    # Verify the invariance rows file.
    rows_path = out_dir / "reports" / f"{run_id}.abx_invariance_tracker_rows.json"
    assert rows_path.exists(), f"missing rows file: {rows_path}"
    rows_data = json.loads(rows_path.read_text(encoding="utf-8"))
    rows = rows_data["rows"]
    assert len(rows) == 3, f"expected 3 rows, got {len(rows)}"
    states = {row["Invariance State"] for row in rows}
    assert "PROVISIONAL" in states or "STABLE" in states, f"unexpected states: {states}"
    provisional_stable = sum(1 for r in rows if r["Invariance State"] in ("PROVISIONAL", "STABLE"))
    assert provisional_stable >= 3, f"expected >= 3 provisional+stable rows, got {provisional_stable}: {states}"