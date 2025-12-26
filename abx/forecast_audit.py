from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from abraxas.evolve.ledger import append_chained_jsonl
from abraxas.forecast.scoring import brier_score


def _parse_dt(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


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


def main() -> int:
    p = argparse.ArgumentParser(description="Forecast Audit v0.1 (Brier per horizon)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    p.add_argument("--audit-ledger", default="out/forecast_ledger/audits.jsonl")
    p.add_argument("--since", default=None, help="ISO start time filter")
    args = p.parse_args()

    preds = _read_jsonl(args.pred_ledger)
    outs = _read_jsonl(args.out_ledger)

    outs_by_id = {}
    for out in outs:
        pred_id = out.get("pred_id")
        if pred_id:
            outs_by_id[str(pred_id)] = out

    since_dt = _parse_dt(args.since) if args.since else None

    by_horizon: Dict[str, Tuple[List[float], List[int]]] = {}
    scored = 0
    for pred in preds:
        pred_id = pred.get("pred_id")
        if not pred_id or str(pred_id) not in outs_by_id:
            continue
        if since_dt:
            ts = _parse_dt(str(pred.get("ts_issued") or "1970-01-01T00:00:00+00:00"))
            if ts < since_dt:
                continue
        out = outs_by_id[str(pred_id)]
        result = str(out.get("result") or "")
        outcome = 1 if result == "hit" else 0
        prob = float(pred.get("p") or 0.5)
        horizon = str(pred.get("horizon") or "weeks")
        by_horizon.setdefault(horizon, ([], []))[0].append(prob)
        by_horizon.setdefault(horizon, ([], []))[1].append(outcome)
        scored += 1

    calibration = {}
    for horizon, (probs, outcomes) in by_horizon.items():
        calibration[horizon] = {"brier": brier_score(probs, outcomes), "n": len(probs)}

    row = {
        "version": "forecast_audit_row.v0.1",
        "run_id": args.run_id,
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "since": args.since,
        "scored": scored,
        "calibration": calibration,
        "provenance": {"method": "abx.forecast_audit.v0.1"},
    }
    append_chained_jsonl(args.audit_ledger, row)
    print(f"[FORECAST_AUDIT] appended audit → {args.audit_ledger} (scored={scored})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
