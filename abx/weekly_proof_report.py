from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate weekly proof report from SIG + calibration + tasks")
    ap.add_argument("--out-reports", default="out/reports")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    sig_path = _latest(args.out_reports, "sig_kpi_*.json")
    cal_path = _latest(args.out_reports, "calibration_report_*.json")
    tasks_path = _latest(args.out_reports, "calibration_tasks_*.json")
    roi_path = _latest(args.out_reports, "signal_roi_plan_*.json")

    sig = _read_json(sig_path) if sig_path else {}
    cal = _read_json(cal_path) if cal_path else {}
    tasks = _read_json(tasks_path) if tasks_path else {}
    roi = _read_json(roi_path) if roi_path else {}

    best = cal.get("best") if isinstance(cal.get("best"), dict) else {}
    top10 = cal.get("top10") if isinstance(cal.get("top10"), list) else []
    tlist = tasks.get("tasks") if isinstance(tasks.get("tasks"), list) else []

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    md = []
    md.append(f"# Weekly Proof Report — {stamp}")
    md.append("")
    md.append("## SIG KPI (scoreboard)")
    md.append(f"- SIG_scalar: **{float(sig.get('SIG_scalar') or 0.0):.3f}**")
    fsg = sig.get("FSG") if isinstance(sig.get("FSG"), dict) else {}
    md.append(f"- Forecast skill deltas: MAE Δ={float(fsg.get('mae_delta') or 0.0):.4f} | Brier Δ={float(fsg.get('brier_delta') or 0.0):.4f}")
    pdg = sig.get("PDG") if isinstance(sig.get("PDG"), dict) else {}
    md.append(f"- Proof density: anchors/term={float(pdg.get('avg_primary_anchors_per_term') or 0.0):.2f} | domains/term={float(pdg.get('avg_unique_domains_per_term') or 0.0):.2f} | fals_tests/term={float(pdg.get('avg_falsification_tests_per_term') or 0.0):.2f}")
    sdg = sig.get("SDG") if isinstance(sig.get("SDG"), dict) else {}
    if sdg.get("slang_bucket_stability") is not None:
        md.append(f"- Slang stability (bucket): {float(sdg.get('slang_bucket_stability') or 0.0):.3f}")
    md.append("")
    md.append("## Calibrated pollution forecast parameters")
    if best:
        md.append(f"- Best scenario: **{best.get('scenario')}** (MRI={best.get('mri')}, IRI={best.get('iri')})")
        md.append(f"- τ_half_life_days: **{best.get('tau_half_life_days')}**")
        md.append(f"- MAE: {best.get('mae')} | Brier(RED within horizon): {best.get('brier_red_within_horizon')}")
    else:
        md.append("- (no calibration report found)")
    md.append("")
    md.append("## Top acquisition tasks (to reduce uncertainty)")
    md.append("| run_id | term | driver | task_type |")
    md.append("|---|---|---|---|")
    for t in tlist[:25]:
        if not isinstance(t, dict):
            continue
        md.append(f"| {t.get('run_id','')} | {t.get('term','')} | {t.get('dominant_driver','')} | {t.get('task_type','')} |")
    md.append("")
    md.append("## Signal ROI plan (what to do next under constraints)")
    if roi:
        summ = roi.get("summary") if isinstance(roi.get("summary"), dict) else {}
        md.append(f"- selected: {int(summ.get('n_selected') or 0)} | spent=${float(summ.get('usd_spent') or 0.0):.2f} | manual={int(summ.get('manual_minutes') or 0)} min")
        md.append("")
        md.append("| rank | term | task_type | roi | usd | min |")
        md.append("|---:|---|---|---:|---:|---:|")
        sel = roi.get("selected") if isinstance(roi.get("selected"), list) else []
        for i, t in enumerate(sel[:12], start=1):
            c = t.get("cost") if isinstance(t.get("cost"), dict) else {}
            md.append(f"| {i} | {t.get('term','')} | {t.get('task_type','')} | {float(t.get('roi') or 0.0):.4f} | {float(c.get('usd') or 0.0):.2f} | {int(c.get('manual_min') or 0)} |")
    else:
        md.append("- (no ROI plan found; run `python -m abx.signal_roi_scheduler`)")
    md.append("")
    md.append("## File pointers")
    md.append(f"- sig_kpi: {sig_path}")
    md.append(f"- calibration_report: {cal_path}")
    md.append(f"- calibration_tasks: {tasks_path}")
    md.append(f"- signal_roi_plan: {roi_path}")
    md.append("")
    md.append("Notes: This report quantifies pollution conditions and evidence strength. It does not label claims true/false.")
    md_txt = "\n".join(md) + "\n"

    out_path = args.out or os.path.join(args.out_reports, f"weekly_proof_report_{stamp}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_txt)
    print(f"[WEEKLY_REPORT] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
