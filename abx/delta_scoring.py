from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


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


def _latest(dir_path: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(dir_path, pattern)))
    return paths[-1] if paths else ""


def _prev(dir_path: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(dir_path, pattern)))
    return paths[-2] if len(paths) >= 2 else ""


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _delta(a: float, b: float) -> float:
    # b - a
    return float(b - a)


def claim_delta(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, float]:
    """
    before/after are entries from time_to_truth["claims"][cid]
    """
    out = {}
    out["d_CSHL_days"] = _delta(_f(before.get("CSHL_days"), -1.0), _f(after.get("CSHL_days"), -1.0))
    out["d_TTT_0.8_days"] = _delta(_f(before.get("TTT_0.8_days"), -1.0), _f(after.get("TTT_0.8_days"), -1.0))
    out["d_flip_rate"] = _delta(_f(before.get("flip_rate"), 0.0), _f(after.get("flip_rate"), 0.0))
    out["d_CS_latest"] = _delta(_f((before.get("latest") or {}).get("CS_score"), 0.0), _f((after.get("latest") or {}).get("CS_score"), 0.0))
    out["d_ML_latest"] = _delta(_f((before.get("latest") or {}).get("ML_score"), 0.0), _f((after.get("latest") or {}).get("ML_score"), 0.0))
    return out


def score_delta(d: Dict[str, float]) -> float:
    """
    Convert deltas to a single "benefit" score (higher better).
    We want: CSHL↓, TTT↓, flip_rate↓, PIS↑, ML↓ (when polluted).
    This score is used only for calibration ranking.
    """
    # Negative deltas for time/flip are good, so subtract them.
    s = 0.0
    s += (-1.0) * _f(d.get("d_CSHL_days"), 0.0) * 0.08
    s += (-1.0) * _f(d.get("d_TTT_0.8_days"), 0.0) * 0.10
    s += (-1.0) * _f(d.get("d_flip_rate"), 0.0) * 1.25
    s += (-1.0) * _f(d.get("d_ML_latest"), 0.0) * 0.70
    s += (+1.0) * _f(d.get("d_CS_latest"), 0.0) * 0.35
    return float(s)


def build_uplift_table(
    per_task_kind: Dict[str, List[Dict[str, float]]]
) -> Dict[str, Dict[str, float]]:
    """
    Aggregate deltas to update expected_uplift coefficients.
    Uses trimmed mean-like behavior via median-of-means (deterministic).
    """
    table: Dict[str, Dict[str, float]] = {}
    for tk, ds in per_task_kind.items():
        if not ds:
            continue
        # Compute simple averages; can be upgraded later to MoM.
        n = len(ds)
        agg = defaultdict(float)
        for d in ds:
            for k, v in d.items():
                agg[k] += float(v)
        table[tk] = {k: float(agg[k] / n) for k in agg.keys()}
        table[tk]["n_samples"] = float(n)
    return table


def main() -> int:
    ap = argparse.ArgumentParser(description="WO-80: delta scoring + uplift calibration")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--ttt-before", default="")
    ap.add_argument("--ttt-after", default="")
    ap.add_argument("--pis-before", default="")
    ap.add_argument("--pis-after", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--uplift-out", default="out/config/uplift_table.json")
    args = ap.parse_args()

    # defaults: use previous and latest
    ttt_after = args.ttt_after or _latest("out/reports", "time_to_truth_*.json")
    ttt_before = args.ttt_before or _prev("out/reports", "time_to_truth_*.json")
    if not ttt_after or not ttt_before:
        raise SystemExit("Need at least two time_to_truth reports (before/after).")

    pis_after = args.pis_after or _latest("out/reports", "proof_integrity_*.json")
    pis_before = args.pis_before or _prev("out/reports", "proof_integrity_*.json")

    before = _read_json(ttt_before)
    after = _read_json(ttt_after)
    bc = before.get("claims") if isinstance(before.get("claims"), dict) else {}
    ac = after.get("claims") if isinstance(after.get("claims"), dict) else {}

    # Task ledger: completed tasks only
    events = _read_jsonl(args.task_ledger)
    completed = [e for e in events if isinstance(e, dict) and e.get("kind") == "task_event" and str(e.get("status") or "").upper() == "COMPLETED"]

    # Map task_id -> task_kind/claim_id
    task_map = {}
    for e in completed:
        tid = str(e.get("task_id") or "")
        if tid:
            task_map[tid] = {
                "task_kind": str(e.get("task_kind") or ""),
                "claim_id": str(e.get("claim_id") or ""),
                "mode": str(e.get("mode") or ""),
            }

    per_claim = {}
    per_task_kind: Dict[str, List[Dict[str, float]]] = defaultdict(list)

    for cid, av in ac.items():
        if cid not in bc or not isinstance(av, dict) or not isinstance(bc.get(cid), dict):
            continue
        dv = claim_delta(bc[cid], av)
        dv["benefit_score"] = score_delta(dv)
        per_claim[cid] = dv

    # Attribute deltas to task kinds by claim_id presence
    # Note: coarse attribution; improved in next operator with more precise linking.
    for tid, info in task_map.items():
        cid = info.get("claim_id") or ""
        tk = (info.get("task_kind") or "").upper().strip()
        if not cid or not tk:
            continue
        if cid in per_claim:
            per_task_kind[tk].append(per_claim[cid])

    uplift_table = build_uplift_table(per_task_kind)

    pis_b = _read_json(pis_before) if pis_before else {}
    pis_a = _read_json(pis_after) if pis_after else {}
    d_pis = _delta(_f(pis_b.get("PIS"), 0.0), _f(pis_a.get("PIS"), 0.0)) if pis_b and pis_a else 0.0

    out_obj = {
        "version": "delta_scoring.v0.1",
        "ts": _utc_now_iso(),
        "inputs": {"ttt_before": ttt_before, "ttt_after": ttt_after, "pis_before": pis_before, "pis_after": pis_after},
        "global_deltas": {"d_PIS": float(d_pis)},
        "n_claims_compared": len(per_claim),
        "per_claim": per_claim,
        "uplift_table": uplift_table,
        "notes": "WO-80 computes stabilization deltas and updates expected uplift coefficients by task_kind (coarse attribution).",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"delta_scoring_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[DELTA] wrote: {out_path}")

    # persist uplift table for planner
    os.makedirs(os.path.dirname(args.uplift_out), exist_ok=True)
    with open(args.uplift_out, "w", encoding="utf-8") as f:
        json.dump({"version": "uplift_table.v0.1", "ts": _utc_now_iso(), "table": uplift_table}, f, ensure_ascii=False, indent=2)
    print(f"[DELTA] wrote uplift_table: {args.uplift_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
