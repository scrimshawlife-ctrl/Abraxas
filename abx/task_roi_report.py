from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="WO-94: summarize task outcomes and ROI by kind")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--outcomes-ledger", default="out/ledger/task_outcomes.jsonl")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    evs = [
        e
        for e in _read_jsonl(args.outcomes_ledger)
        if e.get("kind") == "task_outcome"
        and str(e.get("run_id") or "") == args.run_id
    ]

    by_kind = defaultdict(
        lambda: {"n": 0, "roi_sum": 0.0, "completed": 0, "failed": 0, "offline": 0}
    )
    top = []
    for e in evs:
        tk = str(e.get("task_kind") or "")
        st = str(e.get("status") or "")
        roi = float(e.get("roi") or 0.0)
        by_kind[tk]["n"] += 1
        by_kind[tk]["roi_sum"] += roi
        if st == "COMPLETED":
            by_kind[tk]["completed"] += 1
        elif st == "FAILED":
            by_kind[tk]["failed"] += 1
        elif st == "NEEDS_OFFLINE":
            by_kind[tk]["offline"] += 1
        top.append(
            {
                "task_id": e.get("task_id"),
                "task_kind": tk,
                "claim_id": e.get("claim_id"),
                "term": e.get("term"),
                "status": st,
                "roi": roi,
                "outcome": e.get("outcome") or {},
            }
        )

    kind_rows = []
    for tk, s in by_kind.items():
        n = int(s["n"])
        avg = float(s["roi_sum"] / n) if n else 0.0
        kind_rows.append(
            {
                "task_kind": tk,
                "n": n,
                "avg_roi": avg,
                "completed": int(s["completed"]),
                "failed": int(s["failed"]),
                "offline": int(s["offline"]),
            }
        )
    kind_rows.sort(key=lambda r: (-float(r["avg_roi"]), -int(r["n"]), r["task_kind"]))
    top.sort(key=lambda r: (-float(r["roi"]), r["task_kind"], str(r.get("term") or "")))

    out_obj = {
        "version": "task_roi_report.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "n_events": len(evs),
        "by_kind": kind_rows,
        "top_tasks": top[:25],
        "notes": "ROI is a deterministic heuristic; purpose is to measure which task kinds reduce deficits fastest over time.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"task_roi_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[ROI] wrote: {out_path} events={len(evs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
