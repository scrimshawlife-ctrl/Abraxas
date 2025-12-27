from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


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


def _parse_ts(ts: str) -> Optional[datetime]:
    try:
        if not ts:
            return None
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-85: resolve effective forecast next_review_ts from scheduler ledger"
    )
    ap.add_argument("--forecast-ledger", default="out/ledger/forecast_ledger.jsonl")
    ap.add_argument("--scheduler-ledger", default="out/ledger/scheduler_ledger.jsonl")
    ap.add_argument("--out", default="")
    ap.add_argument("--max", type=int, default=500)
    args = ap.parse_args()

    forecasts = [
        f for f in _read_jsonl(args.forecast_ledger) if f.get("kind") == "forecast"
    ]
    sched = _read_jsonl(args.scheduler_ledger)

    override: Dict[str, Dict[str, Any]] = {}
    for e in sched:
        if not isinstance(e, dict):
            continue
        if e.get("kind") != "forecast_review_scheduled":
            continue
        fid = str(e.get("forecast_id") or "")
        nxt = str(e.get("next_review_ts") or "")
        if not fid or not nxt:
            continue
        override[fid] = {
            "next_review_ts": nxt,
            "ts": e.get("ts"),
            "policy": e.get("policy") if isinstance(e.get("policy"), dict) else {},
        }

    now = datetime.now(timezone.utc).replace(microsecond=0)
    items = []
    for f in forecasts[: int(args.max)]:
        fid = str(f.get("forecast_id") or "")
        base = str(f.get("next_review_ts") or "")
        eff = base
        src = "forecast_ledger"
        pol = {}
        if fid in override:
            eff = str(override[fid].get("next_review_ts") or base)
            src = "scheduler_ledger"
            pol = override[fid].get("policy") or {}

        eff_dt = _parse_ts(eff)
        due = bool(eff_dt and eff_dt <= now)
        items.append(
            {
                "forecast_id": fid,
                "title": f.get("title"),
                "horizon": (f.get("horizon") or {}).get("key"),
                "p": f.get("p"),
                "p_raw": f.get("p_raw"),
                "base_next_review_ts": base,
                "effective_next_review_ts": eff,
                "effective_source": src,
                "due_now": due,
                "policy": pol,
                "run_id": f.get("run_id"),
                "provenance": f.get("provenance"),
                "tags": f.get("tags"),
            }
        )

    def _sort_key(x: Dict[str, Any]) -> tuple:
        dt = _parse_ts(str(x.get("effective_next_review_ts") or "")) or datetime.max.replace(
            tzinfo=timezone.utc
        )
        return (0 if x.get("due_now") else 1, dt)

    items = sorted(items, key=_sort_key)

    obj = {
        "version": "forecast_review_state.v0.1",
        "ts": _utc_now_iso(),
        "n_forecasts": len(items),
        "n_due_now": sum(1 for x in items if x.get("due_now")),
        "items": items,
        "notes": "Derived state: effective next_review_ts is base forecast value overridden by latest scheduler event (if any).",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(
        "out/reports", f"forecast_review_state_{stamp}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[REVIEW_STATE] wrote: {out_path} due_now={obj['n_due_now']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
