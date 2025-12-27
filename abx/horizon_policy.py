from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from abraxas.forecast.horizon_bins import horizon_bucket
from abraxas.forecast.scoring import brier_score


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_jsonl(path: str, max_lines: int = 1500000) -> List[Dict[str, Any]]:
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
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def _dmx_bucket(pr: Dict[str, Any]) -> str:
    ctx = pr.get("context") if isinstance(pr.get("context"), dict) else {}
    dmx = ctx.get("dmx") if isinstance(ctx.get("dmx"), dict) else {}
    bucket = str(dmx.get("bucket") or "").upper().strip()
    return bucket if bucket in ("LOW", "MED", "HIGH") else "UNKNOWN"


ORDER = {"days": 0, "weeks": 1, "months": 2, "years": 3}


def _choose_max_horizon(allowed: Dict[str, bool]) -> str:
    best = "days"
    for horizon in ("weeks", "months", "years"):
        if allowed.get(horizon):
            best = horizon
    return best


def main() -> int:
    p = argparse.ArgumentParser(
        description="Build learned horizon eligibility policy from rolling calibration"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--window-resolved", type=int, default=250)
    p.add_argument("--min-n", type=int, default=20)
    p.add_argument("--brier-days", type=float, default=0.22)
    p.add_argument("--brier-weeks", type=float, default=0.24)
    p.add_argument("--brier-months", type=float, default=0.26)
    p.add_argument("--brier-years", type=float, default=0.28)
    args = p.parse_args()

    ts = _utc_now_iso()
    preds = _read_jsonl(args.pred_ledger)
    outs = _read_jsonl(args.out_ledger)
    outs_by = {str(o.get("pred_id")): o for o in outs if o.get("pred_id")}

    resolved_rows: List[Dict[str, Any]] = []
    for pr in preds:
        pid = pr.get("pred_id")
        if not pid:
            continue
        pid = str(pid)
        oc = outs_by.get(pid)
        if not oc:
            continue
        res = str(oc.get("result") or "")
        y = 1 if res == "hit" else 0
        resolved_rows.append(
            {
                "pred_id": pid,
                "p": float(pr.get("p") or 0.5),
                "y": y,
                "h": horizon_bucket(pr.get("horizon")),
                "dmx": _dmx_bucket(pr),
            }
        )

    window = resolved_rows[-int(args.window_resolved) :] if resolved_rows else []

    by: Dict[str, Dict[str, Tuple[List[float], List[int]]]] = {}
    for row in window:
        b = row["dmx"]
        h = row["h"]
        bh = by.setdefault(b, {})
        bh.setdefault(h, ([], []))[0].append(float(row["p"]))
        bh.setdefault(h, ([], []))[1].append(int(row["y"]))

    roll: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for b, hmap in by.items():
        roll[b] = {}
        for h, (pp, yy) in hmap.items():
            roll[b][h] = {"n": len(pp), "brier": brier_score(pp, yy)}

    thresholds = {
        "days": float(args.brier_days),
        "weeks": float(args.brier_weeks),
        "months": float(args.brier_months),
        "years": float(args.brier_years),
    }

    allowed_by_bucket: Dict[str, Dict[str, Any]] = {}
    max_by_bucket: Dict[str, str] = {}
    rationale: Dict[str, List[str]] = {}

    for b in ("LOW", "MED", "HIGH", "UNKNOWN"):
        allowed = {"days": True, "weeks": False, "months": False, "years": False}
        flags: List[str] = []
        stats = roll.get(b, {})

        for h in ("weeks", "months", "years"):
            st = stats.get(h) or {}
            n = int(st.get("n") or 0)
            br = float(st.get("brier") or 1.0)
            if n < int(args.min_n):
                flags.append(f"INSUFFICIENT_N_{h.upper()}(n={n})")
                allowed[h] = False
                continue
            if br <= thresholds[h]:
                allowed[h] = True
            else:
                allowed[h] = False
                flags.append(f"BRIER_TOO_HIGH_{h.upper()}({br:.3f}>{thresholds[h]:.3f})")

        if b == "HIGH" and allowed.get("years"):
            allowed["years"] = False
            flags.append("HIGH_BUCKET_CLAMP_NO_YEARS")

        allowed_by_bucket[b] = {"allowed": allowed, "max_horizon": _choose_max_horizon(allowed)}
        max_by_bucket[b] = allowed_by_bucket[b]["max_horizon"]
        rationale[b] = flags

    out = {
        "version": "horizon_policy.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "window_resolved": int(args.window_resolved),
        "min_n": int(args.min_n),
        "thresholds": thresholds,
        "rolling_brier": roll,
        "allowed_horizon_max_by_bucket": max_by_bucket,
        "allowed_detail_by_bucket": allowed_by_bucket,
        "rationale_flags_by_bucket": rationale,
        "provenance": {
            "builder": "abx.horizon_policy.v0.1",
            "pred_ledger": args.pred_ledger,
            "out_ledger": args.out_ledger,
        },
    }

    os.makedirs(args.out_reports, exist_ok=True)
    path = os.path.join(args.out_reports, f"horizon_policy_{args.run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[HORIZON_POLICY] wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
