from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _latest(out_reports: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(out_reports, pattern)))
    return paths[-1] if paths else ""


# --- cost model (v0.1 heuristic) ---

TASK_COSTS = {
    "PRIMARY_ANCHOR_SWEEP": {"usd": 1.20, "manual_min": 12},
    "ORIGIN_TIMELINE": {"usd": 0.80, "manual_min": 15},
    "TEMPLATE_CAPTURE": {"usd": 0.10, "manual_min": 18},
    "SYNC_POSTING_CHECK": {"usd": 0.30, "manual_min": 10},
    "AUTH_CHAIN": {"usd": 1.00, "manual_min": 14},
    "DISCONFIRM_TESTS": {"usd": 0.05, "manual_min": 8},
}


def estimate_cost(task: Dict[str, Any], *, decodo_available: bool, decodo_multiplier: float) -> Tuple[float, int]:
    tt = str(task.get("task_type") or "")
    base = TASK_COSTS.get(tt, {"usd": 0.60, "manual_min": 12})
    usd = float(base["usd"])
    manual = int(base["manual_min"])

    mode = str(task.get("mode") or "")
    # If decodo isn't available, online tasks become more manual/time-expensive.
    if ("online" in mode) and (not decodo_available):
        manual = int(manual * 1.6)
        usd = float(usd * 0.25)  # fewer paid calls, more manual labor

    # If decodo is available, assume paid harvesting reduces manual time and increases USD a bit
    if ("online" in mode) and decodo_available:
        usd = float(usd * float(decodo_multiplier))
        manual = max(3, int(manual * 0.70))

    return usd, manual


# --- expected gain model (v0.1 heuristic) ---

def expected_sig_gain(task: Dict[str, Any]) -> float:
    """
    Heuristic E[ΔSIG] in [0, 1-ish].
    Factors:
    - dominant_driver importance: PROV/FOG > TPL > SYN > tests-only
    - term_tpi: high pollution terms offer higher marginal gain
    - ML bucket: likely-manufactured benefits more from anchor/timeline/template capture
    """
    dom = str(task.get("dominant_driver") or "")
    term_tpi = float(task.get("term_tpi") or 0.0)
    ml = task.get("ml") if isinstance(task.get("ml"), dict) else {}
    ml_score = float(ml.get("ml") or 0.0)
    bucket = str(ml.get("bucket") or "UNKNOWN")
    tt = str(task.get("task_type") or "")

    # driver weights
    w_dom = {
        "PROV_GAP": 0.95,
        "FOG": 0.90,
        "TPL": 0.80,
        "SYN": 0.72,
    }.get(dom, 0.60)

    # task-type alignment boost
    align = 0.0
    if tt in ("PRIMARY_ANCHOR_SWEEP", "ORIGIN_TIMELINE") and dom in ("PROV_GAP", "FOG"):
        align += 0.20
    if tt in ("TEMPLATE_CAPTURE", "SYNC_POSTING_CHECK") and (dom == "TPL" or ml_score >= 0.67):
        align += 0.18
    if tt in ("AUTH_CHAIN",) and dom == "SYN":
        align += 0.16
    if tt in ("DISCONFIRM_TESTS",):
        align += 0.10  # small but universally useful

    # bucket boost (manufactured/steered terms yield higher marginal info gain when anchored)
    bucket_boost = 0.0
    if bucket in ("LIKELY_MANUFACTURED", "COORDINATED", "ASTROTURF"):
        bucket_boost = 0.15
    elif bucket in ("MIXED", "UNKNOWN"):
        bucket_boost = 0.06

    # term TPI scales marginal gain
    tpi_scale = 0.35 + 0.85 * min(1.0, max(0.0, term_tpi))

    # ML score modestly increases value of provenance/template work
    ml_scale = 0.90 + 0.25 * min(1.0, max(0.0, ml_score))

    eg = w_dom * tpi_scale * ml_scale + align + bucket_boost
    # bound to 0..1.4 for now
    return float(max(0.0, min(1.4, eg)))


def score_task(
    task: Dict[str, Any],
    *,
    decodo_available: bool,
    decodo_multiplier: float,
    lambda_manual: float,
) -> Dict[str, Any]:
    usd, manual = estimate_cost(task, decodo_available=decodo_available, decodo_multiplier=decodo_multiplier)
    gain = expected_sig_gain(task)
    denom = float(usd + lambda_manual * float(manual) + 1e-6)
    roi = float(gain / denom)
    return {
        **task,
        "roi": roi,
        "expected_gain": gain,
        "cost": {"usd": usd, "manual_min": manual, "lambda_manual": lambda_manual},
        "reason": {
            "dominant_driver": task.get("dominant_driver"),
            "term_tpi": task.get("term_tpi"),
            "ml_bucket": (task.get("ml") or {}).get("bucket") if isinstance(task.get("ml"), dict) else None,
            "ml_score": (task.get("ml") or {}).get("ml") if isinstance(task.get("ml"), dict) else None,
            "task_type": task.get("task_type"),
        },
    }


def build_roi_plan(
    *,
    out_reports: str,
    budget_usd: float,
    max_manual_minutes: int,
    max_tasks: int,
    decodo_available: bool,
    decodo_multiplier: float,
    lambda_manual: float,
) -> Dict[str, Any]:
    tasks_path = _latest(out_reports, "calibration_tasks_*.json")
    tasks_obj = _read_json(tasks_path) if tasks_path else {}
    tasks = tasks_obj.get("tasks") if isinstance(tasks_obj.get("tasks"), list) else []

    scored = [
        score_task(t, decodo_available=decodo_available, decodo_multiplier=decodo_multiplier, lambda_manual=lambda_manual)
        for t in tasks
        if isinstance(t, dict)
    ]
    scored.sort(key=lambda x: (-float(x.get("roi") or 0.0), -float(x.get("expected_gain") or 0.0)))

    # greedy selection under constraints
    picked = []
    spent = 0.0
    manual = 0
    seen = set()  # avoid duplicates (run_id, term, task_type)

    for t in scored:
        if len(picked) >= int(max_tasks):
            break
        key = (str(t.get("run_id") or ""), str(t.get("term") or ""), str(t.get("task_type") or ""))
        if key in seen:
            continue
        c = t.get("cost") if isinstance(t.get("cost"), dict) else {}
        usd = float(c.get("usd") or 0.0)
        mins = int(c.get("manual_min") or 0)

        if (spent + usd) > float(budget_usd):
            continue
        if (manual + mins) > int(max_manual_minutes):
            continue

        picked.append(t)
        seen.add(key)
        spent += usd
        manual += mins

    return {
        "version": "signal_roi_plan.v0.1",
        "ts": _utc_now_iso(),
        "inputs": {
            "out_reports": out_reports,
            "tasks_source": tasks_path,
            "budget_usd": float(budget_usd),
            "max_manual_minutes": int(max_manual_minutes),
            "max_tasks": int(max_tasks),
            "decodo_available": bool(decodo_available),
            "decodo_multiplier": float(decodo_multiplier),
            "lambda_manual": float(lambda_manual),
        },
        "summary": {
            "n_tasks_total": len(scored),
            "n_selected": len(picked),
            "usd_spent": float(spent),
            "manual_minutes": int(manual),
        },
        "selected": picked,
        "ranked_top": scored[:50],
        "notes": "Greedy ROI selection. Costs/gains are heuristic in v0.1; backtest will replace with learned estimators.",
    }


def to_markdown(plan: Dict[str, Any]) -> str:
    s = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    md = []
    md.append("# Signal ROI Plan")
    md.append("")
    md.append(f"- selected: **{int(s.get('n_selected') or 0)}** / {int(s.get('n_tasks_total') or 0)}")
    md.append(f"- spent: **${float(s.get('usd_spent') or 0.0):.2f}**")
    md.append(f"- manual: **{int(s.get('manual_minutes') or 0)} min**")
    md.append("")
    md.append("## Selected tasks")
    md.append("| rank | run_id | term | task_type | driver | roi | gain | usd | min |")
    md.append("|---:|---|---|---|---|---:|---:|---:|---:|")
    sel = plan.get("selected") if isinstance(plan.get("selected"), list) else []
    for i, t in enumerate(sel, start=1):
        c = t.get("cost") if isinstance(t.get("cost"), dict) else {}
        md.append(
            f"| {i} | {t.get('run_id','')} | {t.get('term','')} | {t.get('task_type','')} | {t.get('dominant_driver','')} | "
            f"{float(t.get('roi') or 0.0):.4f} | {float(t.get('expected_gain') or 0.0):.3f} | "
            f"{float(c.get('usd') or 0.0):.2f} | {int(c.get('manual_min') or 0)} |"
        )
    md.append("")
    md.append("## Notes")
    md.append("- ROI is expected_SIG_gain / (usd + λ·manual_minutes).")
    md.append("- This does not execute tasks. It ranks + selects them under constraints.")
    return "\n".join(md) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Signal ROI plan from calibration tasks")
    ap.add_argument("--out-reports", default="out/reports")
    ap.add_argument("--budget-usd", type=float, default=6.0)
    ap.add_argument("--max-manual-minutes", type=int, default=60)
    ap.add_argument("--max-tasks", type=int, default=12)
    ap.add_argument("--decodo-available", action="store_true")
    ap.add_argument("--decodo-multiplier", type=float, default=1.25)
    ap.add_argument("--lambda-manual", type=float, default=0.03, help="USD equivalent per manual minute")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--out-md", default="")
    args = ap.parse_args()

    plan = build_roi_plan(
        out_reports=args.out_reports,
        budget_usd=float(args.budget_usd),
        max_manual_minutes=int(args.max_manual_minutes),
        max_tasks=int(args.max_tasks),
        decodo_available=bool(args.decodo_available),
        decodo_multiplier=float(args.decodo_multiplier),
        lambda_manual=float(args.lambda_manual),
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_json = args.out_json or os.path.join(args.out_reports, f"signal_roi_plan_{stamp}.json")
    out_md = args.out_md or os.path.join(args.out_reports, f"signal_roi_plan_{stamp}.md")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(to_markdown(plan))
    print(f"[ROI_PLAN] wrote: {out_json}")
    print(f"[ROI_PLAN] wrote: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
