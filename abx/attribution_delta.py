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


def _latest(pattern: str) -> str:
    paths = sorted(glob.glob(pattern))
    return paths[-1] if paths else ""


def _prev(pattern: str) -> str:
    paths = sorted(glob.glob(pattern))
    return paths[-2] if len(paths) >= 2 else ""


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _delta(a: float, b: float) -> float:
    return float(b - a)


def claim_delta(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, float]:
    out = {}
    out["d_CSHL_days"] = _delta(_f(before.get("CSHL_days"), -1.0), _f(after.get("CSHL_days"), -1.0))
    out["d_TTT_0.8_days"] = _delta(_f(before.get("TTT_0.8_days"), -1.0), _f(after.get("TTT_0.8_days"), -1.0))
    out["d_flip_rate"] = _delta(_f(before.get("flip_rate"), 0.0), _f(after.get("flip_rate"), 0.0))
    out["d_CS_latest"] = _delta(_f((before.get("latest") or {}).get("CS_score"), 0.0), _f((after.get("latest") or {}).get("CS_score"), 0.0))
    out["d_ML_latest"] = _delta(_f((before.get("latest") or {}).get("ML_score"), 0.0), _f((after.get("latest") or {}).get("ML_score"), 0.0))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="WO-81: attribute deltas using attribution graph (task->edges->claim)")
    ap.add_argument("--attr-graph", default="")
    ap.add_argument("--ttt-before", default="")
    ap.add_argument("--ttt-after", default="")
    ap.add_argument("--uplift-out", default="out/config/uplift_table.json")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    attr_path = args.attr_graph or _latest("out/reports/attribution_graph_*.json")
    if not attr_path:
        raise SystemExit("No attribution_graph found. Run `python -m abx.attribution_compile` first.")

    ttt_after = args.ttt_after or _latest("out/reports/time_to_truth_*.json")
    ttt_before = args.ttt_before or _prev("out/reports/time_to_truth_*.json")
    if not ttt_after or not ttt_before:
        raise SystemExit("Need at least two time_to_truth reports (before/after).")

    attr = _read_json(attr_path)
    tasks = attr.get("tasks") if isinstance(attr.get("tasks"), list) else []

    before = _read_json(ttt_before)
    after = _read_json(ttt_after)
    bc = before.get("claims") if isinstance(before.get("claims"), dict) else {}
    ac = after.get("claims") if isinstance(after.get("claims"), dict) else {}

    # Claim deltas
    deltas_by_claim: Dict[str, Dict[str, float]] = {}
    for cid, av in ac.items():
        if cid in bc and isinstance(av, dict) and isinstance(bc.get(cid), dict):
            deltas_by_claim[cid] = claim_delta(bc[cid], av)

    # Map claim -> tasks that touched it
    claim_to_tasks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for t in tasks:
        if not isinstance(t, dict):
            continue
        meta = t.get("meta") if isinstance(t.get("meta"), dict) else {}
        tk = str(meta.get("task_kind") or "").upper().strip()
        tid = str(t.get("task_id") or "")
        claims_touched = t.get("claims_touched") if isinstance(t.get("claims_touched"), list) else []
        for cid in claims_touched:
            cid = str(cid or "")
            if cid:
                claim_to_tasks[cid].append({"task_id": tid, "task_kind": tk, "n_edges": int(t.get("n_edges") or 0)})

    # Attribution: split delta among tasks touching same claim.
    # Weight by n_edges (more edges -> more credit), deterministic.
    uplift_accum: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    uplift_counts: Dict[str, float] = defaultdict(float)
    per_task_credit = []

    for cid, d in deltas_by_claim.items():
        touched = claim_to_tasks.get(cid, [])
        if not touched:
            continue
        denom = sum(max(1, int(x.get("n_edges") or 1)) for x in touched)
        for x in touched:
            tk = str(x.get("task_kind") or "").upper().strip()
            if not tk:
                continue
            w = float(max(1, int(x.get("n_edges") or 1))) / float(denom)
            uplift_counts[tk] += 1.0
            for k, v in d.items():
                uplift_accum[tk][k] += float(v) * w
            per_task_credit.append({"claim_id": cid, "task_id": x.get("task_id"), "task_kind": tk, "weight": w, "delta": d})

    uplift_table = {}
    for tk, agg in uplift_accum.items():
        n = float(uplift_counts.get(tk) or 0.0)
        if n <= 0:
            continue
        uplift_table[tk] = {k: float(v / n) for k, v in agg.items()}
        uplift_table[tk]["n_samples"] = float(n)

    out_obj = {
        "version": "attribution_delta.v0.1",
        "ts": _utc_now_iso(),
        "inputs": {"attr_graph": attr_path, "ttt_before": ttt_before, "ttt_after": ttt_after},
        "n_claims_with_deltas": len(deltas_by_claim),
        "uplift_table": uplift_table,
        "per_task_credit": per_task_credit[:500],  # cap for size; ledger is source of truth
        "notes": "Edge-weighted attribution of claim deltas to task kinds. Produces calibrated uplift table.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"attribution_delta_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[ATTR_DELTA] wrote: {out_path}")

    os.makedirs(os.path.dirname(args.uplift_out), exist_ok=True)
    with open(args.uplift_out, "w", encoding="utf-8") as f:
        json.dump({"version": "uplift_table.v0.2", "ts": _utc_now_iso(), "table": uplift_table}, f, ensure_ascii=False, indent=2)
    print(f"[ATTR_DELTA] wrote uplift_table: {args.uplift_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
