from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

# horizon_bucket replaced by forecast.horizon.classify capability
from abraxas.forecast.policy_candidates import candidates_v0_1
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


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
                if isinstance(obj, dict):
                    out.append(obj)
            except Exception:
                continue
    return out


def _dmx_bucket(pr: Dict[str, Any]) -> str:
    ctx = pr.get("context") if isinstance(pr.get("context"), dict) else {}
    dmx = ctx.get("dmx") if isinstance(ctx.get("dmx"), dict) else {}
    b = str(dmx.get("bucket") or "").upper().strip()
    return b if b in ("LOW", "MED", "HIGH") else "UNKNOWN"


def _is_shadow(pred_id: str) -> bool:
    return pred_id.endswith("_SHADOW")


ORDER = {"days": 0, "weeks": 1, "months": 2, "years": 3}


def _choose_max_horizon(allowed: Dict[str, bool]) -> str:
    best = "days"
    for h in ("weeks", "months", "years"):
        if allowed.get(h):
            best = h
    return best


def _rolling_stats(window: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    bucket -> horizon -> {n,brier}
    """
    by: Dict[str, Dict[str, Dict[str, Any]]] = {}
    tmp: Dict[str, Dict[str, Dict[str, List[float]]]] = {}
    for r in window:
        b = r["dmx"]
        h = r["h"]
        bh = tmp.setdefault(b, {}).setdefault(h, {"p": [], "y": []})
        bh["p"].append(float(r["p"]))
        bh["y"].append(float(r["y"]))
    for b, hmap in tmp.items():
        by[b] = {}
        for h, d in hmap.items():
            ctx = RuneInvocationContext(run_id="ROLLING_STATS", subsystem_id="abx.horizon_policy_select", git_hash="unknown")
            result = invoke_capability("forecast.scoring.brier", {"probs": d["p"], "outcomes": d["y"]}, ctx=ctx, strict_execution=True)
            by[b][h] = {"n": len(d["p"]), "brier": result.get("brier_score", float("nan"))}
    return by


def main() -> int:
    p = argparse.ArgumentParser(description="Select best horizon policy candidate by measured performance")
    p.add_argument("--run-id", required=True)
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--window-resolved", type=int, default=250)
    p.add_argument("--min-n", type=int, default=20)
    args = p.parse_args()

    ts = _utc_now_iso()
    preds = _read_jsonl(args.pred_ledger)
    outs = _read_jsonl(args.out_ledger)
    outs_by = {str(o.get("pred_id")): o for o in outs if o.get("pred_id")}

    resolved_rows: List[Dict[str, Any]] = []
    pair: Dict[str, Dict[str, Dict[str, Any]]] = {}
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
        row = {
            "pred_id": pid,
            "p": float(pr.get("p") or 0.5),
            "y": y,
            "h": invoke_capability(
                "forecast.horizon.classify",
                {"horizon": pr.get("horizon")},
                ctx=ctx,
                strict_execution=True
            )["horizon_bucket"],
            "dmx": _dmx_bucket(pr),
        }
        resolved_rows.append(row)
        base = pid[:-7] if _is_shadow(pid) else pid
        role = "shadow" if _is_shadow(pid) else "base"
        pair.setdefault(base, {})[role] = row

    window = resolved_rows[-int(args.window_resolved) :] if resolved_rows else []
    roll = _rolling_stats(window)

    shadow_rate: Dict[str, float] = {}
    shadow_counts: Dict[str, List[int]] = {}
    for roles in pair.values():
        if "base" not in roles or "shadow" not in roles:
            continue
        bucket = roles["base"]["dmx"]
        eb = abs(float(roles["base"]["p"]) - float(roles["base"]["y"]))
        es = abs(float(roles["shadow"]["p"]) - float(roles["shadow"]["y"]))
        shadow_counts.setdefault(bucket, [0, 0])[0] += 1
        if es < eb:
            shadow_counts[bucket][1] += 1
    for bucket, (n, sb) in shadow_counts.items():
        shadow_rate[bucket] = float(sb) / float(n) if n else 0.0

    cand = candidates_v0_1()
    results: Dict[str, Any] = {"candidates": cand, "by_bucket": {}}

    def eval_candidate(bucket: str, thr: Dict[str, float]) -> Dict[str, Any]:
        stats = roll.get(bucket, {})
        allowed = {"days": True, "weeks": False, "months": False, "years": False}
        flags: List[str] = []

        for h in ("weeks", "months", "years"):
            st = stats.get(h) or {}
            n = int(st.get("n") or 0)
            br = float(st.get("brier") or 1.0)
            if n < int(args.min_n):
                flags.append(f"INSUFFICIENT_N_{h.upper()}(n={n})")
                allowed[h] = False
            else:
                allowed[h] = br <= float(thr[h])
                if not allowed[h]:
                    flags.append(f"BRIER_TOO_HIGH_{h.upper()}({br:.3f}>{thr[h]:.3f})")

        if bucket == "HIGH" and allowed.get("years"):
            allowed["years"] = False
            flags.append("HIGH_BUCKET_CLAMP_NO_YEARS")

        max_h = _choose_max_horizon(allowed)

        score = 0.0
        weight = 0.0
        for st in stats.values():
            n = int(st.get("n") or 0)
            br = float(st.get("brier") or 1.0)
            score += br * float(n)
            weight += float(n)
        score = score / weight if weight else 1.0

        bonus = float(shadow_rate.get(bucket, 0.0))
        final = float(score) - 0.02 * bonus

        return {
            "allowed": allowed,
            "max_horizon": max_h,
            "rolling_stats": stats,
            "shadow_better_rate": bonus,
            "score": score,
            "final_score": final,
            "flags": flags,
        }

    selected: Dict[str, Any] = {}
    for bucket in ("LOW", "MED", "HIGH", "UNKNOWN"):
        bucket_res: Dict[str, Any] = {}
        best_name = None
        best: Dict[str, Any] | None = None
        for name, thr in cand.items():
            r = eval_candidate(bucket, thr)
            bucket_res[name] = r
            if best is None or r["final_score"] < best["final_score"]:
                best = r
                best_name = name
        results["by_bucket"][bucket] = bucket_res
        selected[bucket] = {
            "selected": best_name,
            "max_horizon": best["max_horizon"],
            "thresholds": cand[best_name],
            "final_score": best["final_score"],
            "flags": best["flags"],
        }

    out_candidates = {
        "version": "horizon_policy_candidates.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "window_resolved": int(args.window_resolved),
        "min_n": int(args.min_n),
        "results": results,
        "provenance": {"builder": "abx.horizon_policy_select.v0.1"},
    }

    out_selected = {
        "version": "horizon_policy_selected.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "selected_by_bucket": selected,
        "provenance": {"builder": "abx.horizon_policy_select.v0.1"},
    }

    os.makedirs(args.out_reports, exist_ok=True)
    p1 = os.path.join(args.out_reports, f"horizon_policy_candidates_{args.run_id}.json")
    p2 = os.path.join(args.out_reports, f"horizon_policy_selected_{args.run_id}.json")
    with open(p1, "w", encoding="utf-8") as f:
        json.dump(out_candidates, f, ensure_ascii=False, indent=2)
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(out_selected, f, ensure_ascii=False, indent=2)
    print(f"[HORIZON_POLICY_SELECT] wrote: {p1}")
    print(f"[HORIZON_POLICY_SELECT] wrote: {p2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
