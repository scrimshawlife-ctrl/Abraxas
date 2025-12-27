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
    bands_path = _latest(args.out_reports, "confidence_bands_*.json")
    regime_path = _latest(args.out_reports, "regime_shift_*.json")
    pis_path = _latest(args.out_reports, "proof_integrity_*.json")
    em_path = _latest(args.out_reports, "evidence_metrics_*.json")
    tm_path = _latest(args.out_reports, "truth_contamination_*.json")
    ttt_path = _latest(args.out_reports, "time_to_truth_*.json")

    sig = _read_json(sig_path) if sig_path else {}
    cal = _read_json(cal_path) if cal_path else {}
    tasks = _read_json(tasks_path) if tasks_path else {}
    roi = _read_json(roi_path) if roi_path else {}
    bands = _read_json(bands_path) if bands_path else {}
    regime = _read_json(regime_path) if regime_path else {}
    pis = _read_json(pis_path) if pis_path else {}
    em = _read_json(em_path) if em_path else {}
    tm = _read_json(tm_path) if tm_path else {}
    ttt = _read_json(ttt_path) if ttt_path else {}

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
    md.append("## Confidence bands (uncertainty)")
    if bands and isinstance(bands.get("bands"), dict):
        b = bands["bands"]
        sigb = b.get("SIG_scalar") if isinstance(b.get("SIG_scalar"), dict) else {}
        md.append(f"- SIG_scalar mean={float(sigb.get('mean') or 0.0):.3f} std={float(sigb.get('std') or 0.0):.3f} latest={float(sigb.get('latest') or 0.0):.3f}")
    else:
        md.append("- (no confidence bands found; run `python -m abx.confidence_bands`)")
    md.append("")
    md.append("## Proof Integrity Score (PIS)")
    if pis:
        md.append(f"- PIS: **{float(pis.get('PIS') or 0.0):.3f}** | dup_rate={float(pis.get('dup_rate') or 0.0):.3f} | domain_entropy_norm={float(pis.get('domain_entropy_norm') or 0.0):.3f} | primary_ratio={float(pis.get('primary_ratio') or 0.0):.3f}")
    else:
        md.append("- (no PIS report found; run `python -m abx.proof_integrity`)")
    md.append("")
    md.append("## Evidence graph metrics (CSS/CPR/SDR)")
    if em and isinstance(em.get("claim_scores"), dict):
        cs = em["claim_scores"]
        # show top 5 most supported claims (CSS high) and top 5 most contested (CPR high)
        top_css = sorted(cs.items(), key=lambda kv: float(kv[1].get("CSS") or 0.0), reverse=True)[:5]
        top_cpr = sorted(cs.items(), key=lambda kv: float(kv[1].get("CPR") or 0.0), reverse=True)[:5]
        md.append("")
        md.append("**Top supported claims (CSS):**")
        for cid, v in top_css:
            md.append(f"- {cid}: CSS={float(v.get('CSS') or 0.0):.3f} | support_w={float(v.get('support_w') or 0.0):.2f} | contra_w={float(v.get('contra_w') or 0.0):.2f} | support_domains={int(v.get('support_domains') or 0)}")
        md.append("")
        md.append("**Most contested claims (CPR):**")
        for cid, v in top_cpr:
            md.append(f"- {cid}: CPR={float(v.get('CPR') or 0.0):.3f} | support_w={float(v.get('support_w') or 0.0):.2f} | contra_w={float(v.get('contra_w') or 0.0):.2f}")
        sdr = em.get("SDR") if isinstance(em.get("SDR"), dict) else {}
        if sdr:
            top_sdr = sorted(sdr.items(), key=lambda kv: float(kv[1] or 0.0), reverse=True)[:8]
            md.append("")
            md.append("**Highest Source Drift (SDR):**")
            for dom, v in top_sdr:
                md.append(f"- {dom}: SDR={float(v):.3f}")
    else:
        md.append("- (no evidence metrics found; run `python -m abx.evidence_graph_compile` and `python -m abx.evidence_metrics`)")
    md.append("")
    md.append("## Truth Contamination Map (Manipulation × Coherence)")
    if tm and isinstance(tm.get("quadrant_counts"), dict):
        qc = tm["quadrant_counts"]
        md.append(f"- Quadrant counts: {qc}")
        md.append("")
        md.append("| claim_id | CS_score | ML_score | quadrant |")
        md.append("|---|---:|---:|---|")
        claims = tm.get("claims") if isinstance(tm.get("claims"), dict) else {}
        # show top 10 by ML_score
        ranked = sorted(claims.items(), key=lambda kv: float((kv[1] or {}).get('ML_score') or 0.0), reverse=True)[:10]
        for cid, v in ranked:
            if not isinstance(v, dict):
                continue
            md.append(f"| {cid} | {float(v.get('CS_score') or 0.0):.3f} | {float(v.get('ML_score') or 0.0):.3f} | {v.get('quadrant','')} |")
    else:
        md.append("- (no truth contamination map found; run `python -m abx.truth_contamination`)")
    md.append("")
    md.append("## Time-to-Truth (TTT) / Claim Stabilization Half-Life (CSHL)")
    if ttt and isinstance(ttt.get("claims"), dict):
        cc = ttt["claims"]
        # show 10 fastest stabilizers (lowest positive CSHL)
        fast = [(cid, v) for cid, v in cc.items() if isinstance(v, dict) and float(v.get("CSHL_days") or -1) >= 0]
        fast = sorted(fast, key=lambda kv: float(kv[1].get("CSHL_days") or 9999))[:10]
        md.append("")
        md.append("| claim_id | CSHL_days | TTT_0.8_days | flip_rate | horizon_class |")
        md.append("|---|---:|---:|---:|---|")
        for cid, v in fast:
            md.append(f"| {cid} | {float(v.get('CSHL_days') or 0.0):.1f} | {float(v.get('TTT_0.8_days') or -1.0):.1f} | {float(v.get('flip_rate') or 0.0):.2f} | {v.get('horizon_class','')} |")
    else:
        md.append("- (no TTT report found; run `python -m abx.claim_timeseries` and `python -m abx.time_to_truth`)")
    md.append("")
    md.append("## Regime shift detector")
    if regime:
        md.append(f"- regime_shift: **{bool(regime.get('regime_shift'))}**")
        md.append(f"- recommendation: {regime.get('recommendation')}")
        fl = regime.get("flags") if isinstance(regime.get("flags"), list) else []
        if fl:
            md.append("")
            md.append("| metric | z | latest | mean | std |")
            md.append("|---|---:|---:|---:|---:|")
            for f in fl[:8]:
                if not isinstance(f, dict):
                    continue
                md.append(f"| {f.get('metric','')} | {float(f.get('z') or 0.0):.2f} | {float(f.get('latest') or 0.0):.3f} | {float(f.get('mean') or 0.0):.3f} | {float(f.get('std') or 0.0):.3f} |")
    else:
        md.append("- (no regime shift report found; run `python -m abx.regime_shift`)")
    md.append("")
    md.append("## File pointers")
    md.append(f"- sig_kpi: {sig_path}")
    md.append(f"- calibration_report: {cal_path}")
    md.append(f"- calibration_tasks: {tasks_path}")
    md.append(f"- signal_roi_plan: {roi_path}")
    md.append(f"- confidence_bands: {bands_path}")
    md.append(f"- regime_shift: {regime_path}")
    md.append(f"- proof_integrity: {pis_path}")
    md.append(f"- evidence_metrics: {em_path}")
    md.append(f"- truth_contamination: {tm_path}")
    md.append(f"- time_to_truth: {ttt_path}")
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
