from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

from abx.run_map import build_run_map


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_day(s: str) -> date:
    return date.fromisoformat(s)


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _run(cmd: List[str]) -> None:
    print("[BACKFILL]", " ".join(cmd))
    subprocess.check_call(cmd)


def _expand_paths(patterns: List[str]) -> List[str]:
    expanded: List[str] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            expanded.extend(matches)
        else:
            expanded.append(pattern)
    return sorted({path for path in expanded})


def main() -> int:
    p = argparse.ArgumentParser(description="Backfill Abraxas daily runs over a date range")
    p.add_argument("--start", required=True, help="YYYY-MM-DD inclusive")
    p.add_argument("--end", required=True, help="YYYY-MM-DD inclusive")
    p.add_argument("--oracle-paths", nargs="+", required=True)
    p.add_argument("--predictions", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--a2-registry", default="out/a2_registry/terms.jsonl")
    p.add_argument("--emit-proof-bundle", action="store_true")
    p.add_argument("--bundle-root", default="out/proof_bundles")
    p.add_argument("--prefix", default="DAILY")
    p.add_argument("--manifest-out", default="out/proof_bundles/backfill_manifest.json")
    args = p.parse_args()

    start = _parse_day(args.start)
    end = _parse_day(args.end)
    if end < start:
        raise SystemExit("end must be >= start")

    oracle_paths = _expand_paths(args.oracle_paths)
    if not oracle_paths:
        raise SystemExit("oracle-paths produced no matches")

    cur = start
    results: List[Dict[str, Any]] = []
    ts0 = _utc_now_iso()

    while cur <= end:
        run_map = build_run_map(cur, oracle_paths, prefix=args.prefix)
        record: Dict[str, Any] = {
            "day": cur.isoformat(),
            "run_id": run_map.run_id,
            "oracle_count": len(run_map.oracle_paths),
        }
        try:
            cmd = [
                "python",
                "-m",
                "abx.daily_run",
                "--run-id",
                run_map.run_id,
                "--oracle-paths",
                *run_map.oracle_paths,
                "--out",
                args.out_reports,
                "--a2-registry",
                args.a2_registry,
                "--predictions",
                args.predictions,
                "--bundle-root",
                args.bundle_root,
            ]
            if args.emit_proof_bundle:
                cmd.append("--emit-proof-bundle")
                record["proof_bundle"] = os.path.join(args.bundle_root, run_map.run_id)
            _run(cmd)
            record["ok"] = True
        except subprocess.CalledProcessError as exc:
            record["ok"] = False
            record["error"] = str(exc)
        results.append(record)
        cur = cur + timedelta(days=1)

    out = {
        "version": "backfill_manifest.v0.1",
        "ts": ts0,
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "results": results,
        "policy": {"non_truncation": True, "labeling_only": True},
    }
    _write_json(args.manifest_out, out)
    print("[BACKFILL] wrote manifest:", args.manifest_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
