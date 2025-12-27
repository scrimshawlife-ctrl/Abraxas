from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def _parse_dt(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_jsonl(path: str, max_lines: int = 500000) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    out.append(obj)
            except Exception:
                continue
    return out


def _outs_index(outcomes_rows: List[Dict[str, Any]]) -> set[str]:
    resolved: set[str] = set()
    for row in outcomes_rows:
        pred_id = row.get("pred_id")
        if pred_id:
            resolved.add(str(pred_id))
    return resolved


def main() -> int:
    p = argparse.ArgumentParser(
        description="Emit due outcomes list (unresolved predictions whose windows ended)"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    p.add_argument(
        "--out-path",
        default=None,
        help="Output JSON path; defaults to out/reports/due_outcomes_<run>.json",
    )
    p.add_argument("--now", default=None)
    p.add_argument("--limit", type=int, default=5000)
    args = p.parse_args()

    now_iso = args.now or _utc_now_iso()
    now = _parse_dt(now_iso)

    preds = _read_jsonl(args.pred_ledger)
    outs = _read_jsonl(args.out_ledger)
    resolved = _outs_index(outs)

    due: List[Dict[str, Any]] = []
    for pred in preds:
        pred_id = pred.get("pred_id")
        if not pred_id:
            continue
        if str(pred_id) in resolved:
            continue
        window_end = pred.get("window_end_ts")
        if not window_end:
            continue
        try:
            end_dt = _parse_dt(str(window_end))
        except Exception:
            continue
        if end_dt <= now:
            due.append(pred)

    due.sort(key=lambda x: str(x.get("window_end_ts") or ""))
    due = due[: int(args.limit)]

    out = {
        "version": "due_outcomes.v0.1",
        "run_id": args.run_id,
        "ts": now_iso,
        "due_count": len(due),
        "due": due,
        "policy": {"non_truncation": True},
    }

    out_path = args.out_path or os.path.join(
        "out", "reports", f"due_outcomes_{args.run_id}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[DUE_OUTCOMES] wrote: {out_path} (n={len(due)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
