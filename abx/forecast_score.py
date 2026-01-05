from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.forecast.scoring import ExpectedErrorBand, brier_score, expected_error_band
from abraxas.forecast.uncertainty import horizon_uncertainty_multiplier


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _apply_eeb_multiplier(eeb: ExpectedErrorBand, multiplier: float) -> Dict[str, Any]:
    mul = max(1.0, float(multiplier))
    eeb_dict = eeb.to_dict()
    eeb_dict["timing_days_min"] = float(eeb_dict["timing_days_min"]) * mul
    eeb_dict["timing_days_max"] = float(eeb_dict["timing_days_max"]) * mul
    eeb_dict["magnitude_pct_min"] = min(0.99, float(eeb_dict["magnitude_pct_min"]) * mul)
    eeb_dict["magnitude_pct_max"] = min(0.99, float(eeb_dict["magnitude_pct_max"]) * mul)
    eeb_dict["multiplier"] = mul
    return eeb_dict


def _scale_eeb_dict(eeb_dict: Dict[str, Any], multiplier: float) -> Dict[str, Any]:
    mul = max(1.0, float(multiplier))
    out = dict(eeb_dict)
    out["timing_days_min"] = float(out.get("timing_days_min") or 0.0) * mul
    out["timing_days_max"] = float(out.get("timing_days_max") or 0.0) * mul
    out["magnitude_pct_min"] = min(0.99, float(out.get("magnitude_pct_min") or 0.0) * mul)
    out["magnitude_pct_max"] = min(0.99, float(out.get("magnitude_pct_max") or 0.0) * mul)
    out["multiplier"] = float(out.get("multiplier") or 1.0) * mul
    return out


def _extract_gate_inputs(a2_phase: Optional[Dict[str, Any]]) -> Dict[str, float]:
    metrics = (a2_phase or {}).get("metrics") if isinstance(a2_phase, dict) else None
    metrics = metrics if isinstance(metrics, dict) else {}
    return {
        "attribution_strength": float(metrics.get("attribution_strength_mean") or 0.0),
        "source_diversity": float(metrics.get("source_diversity_mean") or 0.0),
        "consensus_gap": float(metrics.get("consensus_gap_mean") or 0.0),
        "manipulation_risk_mean": float(metrics.get("manipulation_risk_mean") or 0.0),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Forecast scoring v0.1 (EEB + basic calibration)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--predictions", required=True, help="JSON predictions list (engine output)")
    p.add_argument("--a2-phase", required=False, help="A2 phase artifact to annotate terms")
    p.add_argument("--mwr", default=None, help="MWR artifact path for DMX gating context")
    p.add_argument("--out-reports", default="out/reports")
    args = p.parse_args()

    ts = _utc_now_iso()
    pred = _read_json(args.predictions)
    items = pred.get("predictions") or pred.get("items") or []
    if not isinstance(items, list):
        items = []

    phase_map: Dict[str, Dict[str, Any]] = {}
    a2_phase: Optional[Dict[str, Any]] = None
    if args.a2_phase:
        a2_phase = _read_json(args.a2_phase)
        profiles = a2_phase.get("profiles") or []
        if isinstance(profiles, list):
            for profile in profiles:
                if isinstance(profile, dict) and profile.get("term"):
                    phase_map[str(profile["term"]).lower()] = profile

    gate_inputs = _extract_gate_inputs(a2_phase)
    mwr_path = args.mwr or os.path.join(args.out_reports, f"mwr_{args.run_id}.json")
    ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.forecast_score", git_hash="unknown")
    dmx_result = invoke_capability(
        "memetic.dmx_context.load",
        {"mwr_path": mwr_path},
        ctx=ctx,
        strict_execution=True
    )
    dmx_ctx = dmx_result["dmx_context"]
    dmx_overall = float(dmx_ctx.get("overall_manipulation_risk") or 0.0)
    base_gate_result = invoke_capability(
        "forecast.gating.decide_gate",
        {
            "dmx_overall": dmx_overall,
            "attribution_strength": gate_inputs["attribution_strength"],
            "source_diversity": gate_inputs["source_diversity"],
            "consensus_gap": gate_inputs["consensus_gap"],
            "manipulation_risk_mean": gate_inputs["manipulation_risk_mean"],
        },
        ctx=ctx,
        strict_execution=True
    )
    base_gate = base_gate_result["gate_decision"]

    annotated = []
    probs = []
    outcomes = []
    for item in items:
        if not isinstance(item, dict):
            continue
        horizon = str(item.get("horizon") or "weeks")
        term = str(item.get("term") or item.get("label") or "").strip()
        prob = float(item.get("p") or item.get("probability") or 0.5)
        outcome = item.get("outcome")

        profile = phase_map.get(term.lower()) if term else None
        phase = str((profile or {}).get("phase") or item.get("phase") or "plateau")
        half_life = float((profile or {}).get("half_life_days_fit") or item.get("half_life_days") or 14.0)
        risk = float(
            (profile or {}).get("manipulation_risk_mean")
            or item.get("manipulation_risk")
            or 0.2
        )
        recurrence = (profile or {}).get("recurrence_days")

        gate_result = invoke_capability(
            "forecast.gating.decide_gate",
            {
                "dmx_overall": dmx_overall,
                "attribution_strength": gate_inputs["attribution_strength"],
                "source_diversity": gate_inputs["source_diversity"],
                "consensus_gap": gate_inputs["consensus_gap"],
                "manipulation_risk_mean": risk,
            },
            ctx=ctx,
            strict_execution=True
        )
        gate = gate_result["gate_decision"]
        eeb = expected_error_band(
            horizon=horizon,
            phase=phase,
            half_life_days=half_life,
            manipulation_risk=risk,
            recurrence_days=recurrence if recurrence is None else float(recurrence),
        )
        eeb_dict = _apply_eeb_multiplier(eeb, horizon_uncertainty_multiplier(horizon))
        eeb_dict = _scale_eeb_dict(eeb_dict, float(gate.get("eeb_multiplier") or 1.0))
        out_item = {
            **item,
            "phase": phase,
            "half_life_days_fit": half_life,
            "manipulation_risk_mean": risk,
            "expected_error_band": eeb_dict,
            "gate": gate,
        }
        annotated.append(out_item)

        if outcome is not None:
            probs.append(prob)
            outcomes.append(int(outcome))

    calibration = {}
    if probs and outcomes:
        calibration = {"brier": brier_score(probs, outcomes), "n_scored": len(probs)}

    out_core = {
        "version": "forecast_score.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "inputs": {"predictions": args.predictions, "a2_phase": args.a2_phase},
        "calibration": calibration,
        "gate": base_gate,
        "views": {"annotated_top_30": annotated[:30]},
        "provenance": {"builder": "abx.forecast_score.v0.1"},
    }
    ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.forecast_score", git_hash="unknown")
    result = invoke_capability(
        "evolve.policy.enforce_non_truncation",
        {"artifact": out_core, "raw_full": {"annotated": list(annotated)}},
        ctx=ctx,
        strict_execution=True
    )
    out = result["artifact"]

    jpath = os.path.join(args.out_reports, f"forecast_score_{args.run_id}.json")
    mpath = os.path.join(args.out_reports, f"forecast_score_{args.run_id}.md")
    _write_json(jpath, out)
    with open(mpath, "w", encoding="utf-8") as f:
        f.write("# Forecast Scoring v0.1\n\n")
        f.write(f"- run_id: `{args.run_id}`\n- ts: `{ts}`\n\n")
        if calibration:
            f.write(
                "## Calibration\n"
                f"- Brier: `{calibration.get('brier')}`\n"
                f"- n_scored: `{calibration.get('n_scored')}`\n\n"
            )
        f.write("## Annotated predictions (top 30)\n")
        for item in annotated[:30]:
            eeb = item.get("expected_error_band") or {}
            f.write(
                f"- **{item.get('term') or item.get('label')}** horizon={item.get('horizon')} "
                f"p={item.get('p') or item.get('probability')} phase={item.get('phase')} "
                f"risk={item.get('manipulation_risk_mean'):.2f} "
                f"EEB_timing_days=[{eeb.get('timing_days_min'):.1f},{eeb.get('timing_days_max'):.1f}] "
                f"EEB_mag=[{eeb.get('magnitude_pct_min'):.2f},{eeb.get('magnitude_pct_max'):.2f}]\n"
            )

    print(f"[FORECAST_SCORE] wrote: {jpath}")
    print(f"[FORECAST_SCORE] wrote: {mpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
