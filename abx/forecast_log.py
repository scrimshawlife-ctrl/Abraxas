from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from abraxas.forecast.horizon_policy import compare_horizon, enforce_horizon_policy
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.forecast.term_class_map import load_term_class_map
from abraxas.forecast.ledger import issue_prediction
from abraxas.conspiracy.policy import csp_horizon_clamp, apply_horizon_cap
from abraxas.memetic.term_index import build_term_index, reduce_weighted_metrics


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def main() -> int:
    p = argparse.ArgumentParser(description="Forecast Log v0.1 (append predictions to ledger)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--forecast-score", required=True, help="forecast_score_<run>.json output")
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--mwr", default=None, help="MWR artifact path to stamp DMX context")
    args = p.parse_args()

    forecast_score = _read_json(args.forecast_score)
    annotated = forecast_score.get("annotated")
    if annotated is None:
        raw_full = forecast_score.get("raw_full") or {}
        annotated = raw_full.get("annotated")
    if not isinstance(annotated, list):
        annotated = []

    mwr_path = args.mwr or os.path.join("out", "reports", f"mwr_{args.run_id}.json")
    ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.forecast_log", git_hash="unknown")
    dmx_result = invoke_capability(
        "memetic.dmx_context.load",
        {"mwr_path": mwr_path},
        ctx=ctx,
        strict_execution=True
    )
    dmx_ctx = dmx_result["dmx_context"]
    dmx_overall = float(dmx_ctx.get("overall_manipulation_risk") or 0.0)
    dmx_bucket = str(dmx_ctx.get("bucket") or "LOW").upper()

    policy_tc_path = os.path.join("out", "reports", f"horizon_policy_selected_tc_{args.run_id}.json")
    policy_path = os.path.join("out", "reports", f"horizon_policy_selected_{args.run_id}.json")
    policy_tc: Dict[str, Any] = {}
    policy: Dict[str, Any] = {}
    if os.path.exists(policy_tc_path):
        try:
            policy_tc = _read_json(policy_tc_path)
        except Exception:
            policy_tc = {}
    if os.path.exists(policy_path):
        try:
            policy = _read_json(policy_path)
        except Exception:
            policy = {}
    a2_path = os.path.join("out", "reports", f"a2_phase_{args.run_id}.json")
    term_class = load_term_class_map(a2_path)
    term_csp: Dict[str, Any] = {}
    try:
        if os.path.exists(a2_path):
            with open(a2_path, "r", encoding="utf-8") as f:
                a2_json = json.load(f)
            raw = a2_json.get("raw_full") if isinstance(a2_json, dict) else {}
            profiles = (
                raw.get("profiles")
                if isinstance(raw, dict) and isinstance(raw.get("profiles"), list)
                else None
            )
            if isinstance(profiles, list):
                for profile in profiles:
                    if not isinstance(profile, dict):
                        continue
                    term_key = str(profile.get("term") or "").strip().lower()
                    csp = profile.get("term_csp_summary")
                    if term_key and isinstance(csp, dict):
                        term_csp[term_key] = csp
    except Exception:
        term_csp = {}

    selected = (policy.get("selected_by_bucket") or {}) if isinstance(policy, dict) else {}
    cap_by_bucket = {
        b: (v.get("max_horizon") if isinstance(v, dict) else None) for b, v in selected.items()
    }
    sel_tc = (
        policy_tc.get("selected_by_bucket_and_class") or {}
        if isinstance(policy_tc, dict)
        else {}
    )

    a2_path = os.path.join("out", "reports", f"a2_phase_{args.run_id}.json")
    a2: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    try:
        if os.path.exists(a2_path):
            with open(a2_path, "r", encoding="utf-8") as f:
                a2 = json.load(f)
            if isinstance(a2, dict) and isinstance(a2.get("metrics"), dict):
                metrics = a2.get("metrics") or {}
    except Exception:
        metrics = {}
    term_idx = build_term_index(a2) if isinstance(a2, dict) else {}

    wrote = 0
    for item in annotated:
        if not isinstance(item, dict):
            continue
        term = str(item.get("term") or item.get("label") or "").strip()
        if not term:
            continue
        horizon = str(item.get("horizon") or "weeks")
        prob = float(item.get("p") or item.get("probability") or 0.5)
        terms = []
        if isinstance(item.get("terms"), list):
            terms = [str(x) for x in item.get("terms") if str(x).strip()]
        elif term:
            terms = [term]

        weighted = reduce_weighted_metrics(terms, term_idx) if terms else {"matched_terms": 0.0}
        matched = bool(weighted.get("matched_terms"))
        has_attr = float(weighted.get("attribution_strength_count") or 0.0) > 0
        has_sd = float(weighted.get("source_diversity_count") or 0.0) > 0
        has_cg = float(weighted.get("consensus_gap_count") or 0.0) > 0
        has_mr = float(weighted.get("manipulation_risk_count") or 0.0) > 0
        att = (
            float(weighted.get("attribution_strength_mean") or 0.0)
            if matched and has_attr
            else float(metrics.get("attribution_strength_mean") or 0.0)
        )
        sd = (
            float(weighted.get("source_diversity_mean") or 0.0)
            if matched and has_sd
            else float(metrics.get("source_diversity_mean") or 0.0)
        )
        cg = (
            float(weighted.get("consensus_gap_mean") or 0.0)
            if matched and has_cg
            else float(metrics.get("consensus_gap_mean") or 0.0)
        )
        mr = (
            float(weighted.get("manipulation_risk_mean") or 0.0)
            if matched and has_mr
            else float(metrics.get("manipulation_risk_mean") or 0.0)
        )

        ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.forecast_log", git_hash="unknown")
        gate_result = invoke_capability(
            "forecast.gating.decide_gate",
            {
                "dmx_overall": dmx_overall,
                "attribution_strength": att,
                "source_diversity": sd,
                "consensus_gap": cg,
                "manipulation_risk_mean": mr,
            },
            ctx=ctx,
            strict_execution=True
        )
        gate = gate_result["gate_decision"]
        primary_term = str(item.get("term") or "").strip().lower()
        if not primary_term:
            tl = item.get("terms") if isinstance(item.get("terms"), list) else []
            if tl:
                primary_term = str(tl[0]).strip().lower()
        tcls = term_class.get(primary_term, "unknown") if primary_term else "unknown"
        csp = term_csp.get(primary_term, {}) if primary_term else {}

        policy_cap = None
        if isinstance(sel_tc, dict):
            bucket_map = sel_tc.get(dmx_bucket)
            if isinstance(bucket_map, dict):
                cell = bucket_map.get(tcls)
                if isinstance(cell, dict):
                    policy_cap = cell.get("max_horizon")
        if not policy_cap:
            policy_cap = cap_by_bucket.get(dmx_bucket) or cap_by_bucket.get("UNKNOWN")
        csp_cap, csp_flags = csp_horizon_clamp(
            csp=csp,
            dmx_bucket=dmx_bucket,
            term_class=tcls,
        )
        final_cap = apply_horizon_cap(policy_cap=policy_cap, csp_cap=csp_cap)
        if final_cap and compare_horizon(gate.get("horizon_max"), final_cap) > 0:
            gate["horizon_max"] = final_cap
            gate.setdefault("flags", []).append("POLICY_HORIZON_MAX")
            gate.setdefault("provenance", {})["policy"] = (
                policy_tc_path if policy_tc else policy_path
            )
        if csp_flags:
            gate_flags = gate.get("flags") if isinstance(gate.get("flags"), list) else []
            gate["flags"] = gate_flags + csp_flags
        flags, shadow_horizon = enforce_horizon_policy(
            horizon=horizon, gate=gate, emit_shadow=True
        )
        base_context = {
            "dmx": dict(dmx_ctx),
            "gate": gate,
            "gate_inputs": {"terms": terms, "weighted_metrics": weighted},
        }
        row = issue_prediction(
            term=term,
            p=prob,
            horizon=horizon,
            run_id=args.run_id,
            expected_error_band=item.get("expected_error_band") or {},
            phase_context={
                "phase": item.get("phase"),
                "half_life_days_fit": item.get("half_life_days_fit"),
                "manipulation_risk_mean": item.get("manipulation_risk_mean"),
            },
            evidence=item.get("evidence") or [],
            context=base_context,
            flags=flags,
            ledger_path=args.pred_ledger,
        )
        wrote += 1
        if shadow_horizon:
            shadow_flags = list(flags) + ["SHADOW_CONSTRAINED_HORIZON"]
            shadow_context = {
                **base_context,
                "shadow_of": row.get("pred_id"),
            }
            issue_prediction(
                term=term,
                p=prob,
                horizon=shadow_horizon,
                run_id=args.run_id,
                expected_error_band=item.get("expected_error_band") or {},
                phase_context={
                    "phase": item.get("phase"),
                    "half_life_days_fit": item.get("half_life_days_fit"),
                    "manipulation_risk_mean": item.get("manipulation_risk_mean"),
                },
                evidence=item.get("evidence") or [],
                context=shadow_context,
                flags=shadow_flags,
                ledger_path=args.pred_ledger,
            )
            wrote += 1

    print(f"[FORECAST_LOG] appended {wrote} predictions → {args.pred_ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
