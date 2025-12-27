from __future__ import annotations

import argparse
import glob
import os
import subprocess
from datetime import datetime, timedelta, timezone
from typing import List, Tuple


def _list_run_ids(out_reports: str, days: int) -> List[str]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    paths = sorted(glob.glob(os.path.join(out_reports, "a2_phase_*.json")))
    runs: List[Tuple[float, str]] = []
    for path in paths:
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
            if mtime < cutoff:
                continue
            rid = path.split("a2_phase_", 1)[-1].replace(".json", "")
            runs.append((mtime.timestamp(), rid))
        except Exception:
            continue
    runs.sort(key=lambda x: (x[0], x[1]))
    return [rid for _, rid in runs]


def run(cmd: List[str]) -> None:
    print("[REPLAY]", " ".join(cmd))
    subprocess.run(cmd, check=False)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Replay last N days: compute evidence uplift then regenerate A2 + MWR enrichment"
    )
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--ledger", default="out/ledger/evidence_ledger.jsonl")
    p.add_argument("--registry", default="out/a2_registry/terms.jsonl")
    args = p.parse_args()

    run_ids = _list_run_ids(args.out_reports, int(args.days))
    print(f"[REPLAY] runs={len(run_ids)}")

    for rid in run_ids:
        run(
            [
                "python",
                "-m",
                "abx.evidence_uplift",
                "--run-id",
                rid,
                "--out-reports",
                args.out_reports,
                "--ledger",
                args.ledger,
            ]
        )
        run(
            [
                "python",
                "-m",
                "abx.a2_phase",
                "--run-id",
                rid,
                "--registry",
                args.registry,
                "--out-reports",
                args.out_reports,
                "--mwr",
                os.path.join(args.out_reports, f"mwr_{rid}.json"),
            ]
        )
        run(
            [
                "python",
                "-m",
                "abx.mwr_enrich",
                "--run-id",
                rid,
                "--out-reports",
                args.out_reports,
                "--ledger",
                args.ledger,
            ]
        )
        run(
            [
                "python",
                "-m",
                "abx.truth_pollution",
                "--run-id",
                rid,
                "--out-reports",
                args.out_reports,
                "--ledger",
                args.ledger,
            ]
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
