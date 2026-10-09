from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Produce invariance tracker rows until >= 3 are PROVISIONAL or STABLE."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts_seal/runs"))
    parser.add_argument("--report-dir", type=Path, default=Path("out/reports"))
    parser.add_argument("--ledger-path", type=Path, default=Path("out/ledger/abx_invariance_tracker.jsonl"))
    return parser.parse_args()


def _count_provisional_stable(rows: list[dict]) -> int:
    return sum(1 for r in rows if r.get("Invariance State") in ("PROVISIONAL", "STABLE"))


def main() -> int:
    args = parse_args()
    report_path = args.report_dir / f"{args.run_id}.abx_invariance_tracker_rows.json"

    base_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "log_gap_closure_invariance.py"),
        "--run-id",
        args.run_id,
        "--mode",
        "sandbox",
        "--workspace-scope",
        "workspace_only",
        "--artifacts-dir",
        args.artifacts_dir.as_posix(),
        "--ledger-path",
        args.ledger_path.as_posix(),
        "--report-path",
        report_path.as_posix(),
    ]

    # Pass 1: generate UNCHECKED rows (or load from existing ledger).
    r1 = subprocess.run(base_cmd, check=False, capture_output=True, text=True)
    if r1.returncode != 0:
        print(f"producer: pass 1 failed (exit {r1.returncode}): {r1.stderr}", file=sys.stderr)
        return r1.returncode

    # Pass 2: transition UNCHECKED → PROVISIONAL (ledger compare finds MATCH).
    r2 = subprocess.run(base_cmd, check=False, capture_output=True, text=True)
    if r2.returncode != 0:
        print(f"producer: pass 2 failed (exit {r2.returncode}): {r2.stderr}", file=sys.stderr)
        return r2.returncode

    # Verify the result.
    if not report_path.exists():
        print(f"producer: rows file not found at {report_path}", file=sys.stderr)
        return 1

    rows_data = json.loads(report_path.read_text(encoding="utf-8"))
    rows = rows_data.get("rows", [])
    count = _count_provisional_stable(rows)
    if count < 3:
        print(
            f"producer: only {count} PROVISIONAL/STABLE rows (need >= 3). "
            f"States: {[r.get('Invariance State') for r in rows]}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())