from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from abraxas.forecast.horizon_bins import horizon_bucket
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_jsonl(path: str, max_lines: int = 1200000) -> List[Dict[str, Any]]:
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


def _dmx_bucket(pred: Dict[str, Any]) -> str:
    ctx = pred.get("context") if isinstance(pred.get("context"), dict) else {}
    dmx = ctx.get("dmx") if isinstance(ctx.get("dmx"), dict) else {}
    bucket = str(dmx.get("bucket") or "").upper().strip()
    return bucket if bucket in ("LOW", "MED", "HIGH") else "UNKNOWN"


def _is_shadow(pred_id: str) -> bool:
    return pred_id.endswith("_SHADOW")


def _sharpness(ps: List[float]) -> float:
    if not ps:
        return 0.0
    return float(sum(abs(p - 0.5) for p in ps) / float(len(ps)))


def main() -> int:
    p = argparse.ArgumentParser(
        description="Horizon audit: calibration + sharpness + shadow dominance"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    p.add_argument("--out-reports", default="out/reports")
    args = p.parse_args()

    ts = _utc_now_iso()
    preds = _read_jsonl(args.pred_ledger)
    outs = _read_jsonl(args.out_ledger)
    outs_by = {str(o.get("pred_id")): o for o in outs if o.get("pred_id")}

    by_h: Dict[str, Tuple[List[float], List[int]]] = {}
    by_h_dmx: Dict[str, Dict[str, Tuple[List[float], List[int]]]] = {}

    resolved = 0
    unresolved = 0

    pair: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for pred in preds:
        pred_id = pred.get("pred_id")
        if not pred_id:
            continue
        pred_id = str(pred_id)
        out = outs_by.get(pred_id)
        if not out:
            unresolved += 1
            continue
        result = str(out.get("result") or "")
        y = 1 if result == "hit" else 0
        p0 = float(pred.get("p") or 0.5)
        horizon = horizon_bucket(pred.get("horizon"))
        dmx_b = _dmx_bucket(pred)

        by_h.setdefault(horizon, ([], []))[0].append(p0)
        by_h.setdefault(horizon, ([], []))[1].append(y)
        bh = by_h_dmx.setdefault(dmx_b, {})
        bh.setdefault(horizon, ([], []))[0].append(p0)
        bh.setdefault(horizon, ([], []))[1].append(y)
        resolved += 1

        base = pred_id[:-7] if _is_shadow(pred_id) else pred_id
        role = "shadow" if _is_shadow(pred_id) else "base"
        pair.setdefault(base, {})[role] = {"p": p0, "y": y, "h": horizon, "dmx": dmx_b}

    calibration = {}
    for h, (pp, yy) in by_h.items():
        ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.horizon_audit", git_hash="unknown")
        result = invoke_capability("forecast.scoring.brier", {"probs": pp, "outcomes": yy}, ctx=ctx, strict_execution=True)
        calibration[h] = {"n": len(pp), "brier": result.get("brier_score", float("nan")), "sharpness": _sharpness(pp)}

    calibration_by_bucket: Dict[str, Any] = {}
    for bucket, hmap in by_h_dmx.items():
        bucket_cal = {}
        for h, (pp, yy) in hmap.items():
            ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.horizon_audit", git_hash="unknown")
            result = invoke_capability("forecast.scoring.brier", {"probs": pp, "outcomes": yy}, ctx=ctx, strict_execution=True)
            bucket_cal[h] = {"n": len(pp), "brier": result.get("brier_score", float("nan")), "sharpness": _sharpness(pp)}
        calibration_by_bucket[bucket] = bucket_cal

    shadow_cmp = {"n_pairs": 0, "shadow_better": 0, "base_better": 0, "tie": 0}
    for base_id, roles in pair.items():
        if "base" not in roles or "shadow" not in roles:
            continue
        shadow_cmp["n_pairs"] += 1
        eb = abs(float(roles["base"]["p"]) - float(roles["base"]["y"]))
        es = abs(float(roles["shadow"]["p"]) - float(roles["shadow"]["y"]))
        if es < eb:
            shadow_cmp["shadow_better"] += 1
        elif eb < es:
            shadow_cmp["base_better"] += 1
        else:
            shadow_cmp["tie"] += 1

    out_obj = {
        "version": "horizon_audit.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "resolved": resolved,
        "unresolved": unresolved,
        "calibration": calibration,
        "calibration_by_dmx_bucket": calibration_by_bucket,
        "shadow_dominance": shadow_cmp,
        "provenance": {
            "builder": "abx.horizon_audit.v0.1",
            "pred_ledger": args.pred_ledger,
            "out_ledger": args.out_ledger,
        },
    }

    os.makedirs(args.out_reports, exist_ok=True)
    path = os.path.join(args.out_reports, f"horizon_audit_{args.run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[HORIZON_AUDIT] wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
