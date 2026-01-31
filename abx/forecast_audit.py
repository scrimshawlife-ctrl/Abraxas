from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


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
    p.add_argument("--out-reports", default="out/reports")
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
    by_bucket: Dict[str, Dict[str, Tuple[List[float], List[int]]]] = {}
    bucket_counts: Dict[str, int] = {}

    def _get_bucket(pred: Dict[str, Any]) -> str:
        ctx = pred.get("context") or {}
        if isinstance(ctx, dict):
            dmx = ctx.get("dmx") or {}
            if isinstance(dmx, dict):
                bucket = str(dmx.get("bucket") or "").upper().strip()
                if bucket in ("LOW", "MED", "HIGH"):
                    return bucket
        return "UNKNOWN"
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

        bucket = _get_bucket(pred)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        by_bucket.setdefault(bucket, {}).setdefault(horizon, ([], []))[0].append(prob)
        by_bucket.setdefault(bucket, {}).setdefault(horizon, ([], []))[1].append(outcome)
        scored += 1

    calibration = {}
    for horizon, (probs, outcomes) in by_horizon.items():
        ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.forecast_audit", git_hash="unknown")
        result = invoke_capability("forecast.scoring.brier", {"probs": probs, "outcomes": outcomes}, ctx=ctx, strict_execution=True)
        calibration[horizon] = {"brier": result.get("brier_score", float("nan")), "n": len(probs)}

    calibration_by_bucket: Dict[str, Any] = {}
    for bucket, horizons in by_bucket.items():
        bucket_metrics: Dict[str, Any] = {}
        for horizon, (probs, outcomes) in horizons.items():
            ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.forecast_audit", git_hash="unknown")
            result = invoke_capability("forecast.scoring.brier", {"probs": probs, "outcomes": outcomes}, ctx=ctx, strict_execution=True)
            bucket_metrics[horizon] = {
                "brier": result.get("brier_score", float("nan")),
                "n": len(probs),
            }
        calibration_by_bucket[bucket] = bucket_metrics

    row = {
        "version": "forecast_audit_row.v0.1",
        "run_id": args.run_id,
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "since": args.since,
        "scored": scored,
        "calibration": calibration,
        "calibration_by_bucket": calibration_by_bucket,
        "coverage_by_bucket": bucket_counts,
        "provenance": {"method": "abx.forecast_audit.v0.1"},
    }
    # Use capability contract for ledger append
    ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.forecast_audit", git_hash="unknown")
    invoke_capability("evolve.ledger.append", {"path": args.audit_ledger, "record": row}, ctx=ctx, strict_execution=True)
    json_path = os.path.join(args.out_reports, f"forecast_audit_{args.run_id}.json")
    md_path = os.path.join(args.out_reports, f"forecast_audit_{args.run_id}.md")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(row, f, ensure_ascii=False, indent=2, sort_keys=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Forecast Audit v0.1\n\n")
        f.write(f"- run_id: `{args.run_id}`\n")
        f.write(f"- ts: `{row['ts']}`\n")
        f.write(f"- since: `{args.since}`\n")
        f.write(f"- scored: `{scored}`\n\n")
        f.write("## Calibration (Brier per horizon)\n")
        for horizon, metrics in calibration.items():
            f.write(
                f"- **{horizon}** brier={metrics.get('brier')} n={metrics.get('n')}\n"
            )
    print(f"[FORECAST_AUDIT] wrote {json_path}")
    print(f"[FORECAST_AUDIT] wrote {md_path}")
    print(f"[FORECAST_AUDIT] appended audit → {args.audit_ledger} (scored={scored})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
