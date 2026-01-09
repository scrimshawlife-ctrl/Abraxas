from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

# horizon_bucket replaced by forecast.horizon.classify capability
# load_term_class_map replaced by forecast.term_class_map.load capability
# candidates_v0_1 replaced by forecast.policy.candidates_v0_1 capability
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


def _term_key(pr: Dict[str, Any]) -> str:
    t = str(pr.get("term") or "").strip()
    if t:
        return t.lower()
    ts = pr.get("terms") if isinstance(pr.get("terms"), list) else []
    if ts:
        return str(ts[0]).strip().lower()
    return ""


def _rolling_stats(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]:
    """
    bucket -> class -> horizon -> {n,brier}
    """
    tmp: Dict[str, Dict[str, Dict[str, Dict[str, List[float]]]]] = {}
    for r in rows:
        b = r["dmx"]
        c = r["class"]
        h = r["h"]
        cell = tmp.setdefault(b, {}).setdefault(c, {}).setdefault(h, {"p": [], "y": []})
        cell["p"].append(float(r["p"]))
        cell["y"].append(float(r["y"]))

    out: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}
    for b, cmap in tmp.items():
        out[b] = {}
        for c, hmap in cmap.items():
            out[b][c] = {}
            for h, d in hmap.items():
                ctx = RuneInvocationContext(run_id="ROLLING_STATS_TC", subsystem_id="abx.horizon_policy_select_tc", git_hash="unknown")
                result = invoke_capability("forecast.scoring.brier", {"probs": d["p"], "outcomes": d["y"]}, ctx=ctx, strict_execution=True)
                out[b][c][h] = {"n": len(d["p"]), "brier": result.get("brier_score", float("nan"))}
    return out


def main() -> int:
    p = argparse.ArgumentParser(
        description="Select best horizon policy per (DMX bucket × term class)"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--a2-phase", default=None)
    p.add_argument("--window-resolved", type=int, default=400)
    p.add_argument("--min-n", type=int, default=15)
    args = p.parse_args()

    ts = _utc_now_iso()
    preds = _read_jsonl(args.pred_ledger)
    outs = _read_jsonl(args.out_ledger)
    outs_by = {str(o.get("pred_id")): o for o in outs if o.get("pred_id")}

    a2_path = args.a2_phase or os.path.join(args.out_reports, f"a2_phase_{args.run_id}.json")
    # Create context for capability invocations
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.horizon_policy_select_tc",
        git_hash="unknown"
    )
    term_class = invoke_capability(
        "forecast.term_class_map.load",
        {"a2_phase_path": a2_path},
        ctx=ctx,
        strict_execution=True
    )["term_class_map"]

    resolved: List[Dict[str, Any]] = []
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
        tk = _term_key(pr)
        cls = term_class.get(tk, "unknown") if tk else "unknown"
        resolved.append(
            {
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
                "class": cls,
            }
        )

    window = resolved[-int(args.window_resolved) :] if resolved else []
    roll = _rolling_stats(window)

    # Load policy candidates via capability contract
    ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.horizon_policy_select_tc", git_hash="unknown")
    cand_result = invoke_capability(
        "forecast.policy.candidates_v0_1",
        {},
        ctx=ctx,
        strict_execution=True
    )
    cand = cand_result["candidates"]
    buckets = ("LOW", "MED", "HIGH", "UNKNOWN")
    classes = ("stable", "emerging", "volatile", "contested", "unknown")

    def choose_max(allowed: Dict[str, bool]) -> str:
        best = "days"
        for h in ("weeks", "months", "years"):
            if allowed.get(h):
                best = h
        return best

    results: Dict[str, Any] = {"candidates": cand, "roll": roll, "selected": {}}

    for b in buckets:
        results["selected"][b] = {}
        for c in classes:
            stats = ((roll.get(b) or {}).get(c) or {})
            best_name = None
            best_final = None
            best_max = "days"
            best_flags: List[str] = []

            for name, thr in cand.items():
                flags: List[str] = []
                allowed = {"days": True, "weeks": False, "months": False, "years": False}

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

                if b == "HIGH" and c in ("contested", "volatile") and allowed.get("years"):
                    allowed["years"] = False
                    flags.append("HIGH_FOG_CLAMP_NO_YEARS_FOR_VOLATILE_OR_CONTESTED")

                score = 1.0
                w = 0.0
                s = 0.0
                for st in stats.values():
                    n = int(st.get("n") or 0)
                    br = float(st.get("brier") or 1.0)
                    s += br * float(n)
                    w += float(n)
                if w:
                    score = s / w

                order = {"days": 0, "weeks": 1, "months": 2, "years": 3}
                max_h = choose_max(allowed)
                coverage_bonus = 0.01 * float(order.get(max_h, 0))
                final = float(score) - coverage_bonus

                if best_final is None or final < best_final:
                    best_final = final
                    best_name = name
                    best_max = max_h
                    best_flags = flags

            results["selected"][b][c] = {
                "selected": best_name,
                "max_horizon": best_max,
                "thresholds": cand.get(best_name or "balanced"),
                "final_score": best_final,
                "flags": best_flags,
            }

    out = {
        "version": "horizon_policy_selected_tc.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "selected_by_bucket_and_class": results["selected"],
        "provenance": {"builder": "abx.horizon_policy_select_tc.v0.1", "a2_phase": a2_path},
    }

    os.makedirs(args.out_reports, exist_ok=True)
    path = os.path.join(args.out_reports, f"horizon_policy_selected_tc_{args.run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[HORIZON_POLICY_SELECT_TC] wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
