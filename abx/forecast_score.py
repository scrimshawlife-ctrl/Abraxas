from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from abraxas.evolve.non_truncation import enforce_non_truncation
from abraxas.forecast.scoring import brier_score, expected_error_band


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


def main() -> int:
    p = argparse.ArgumentParser(description="Forecast scoring v0.1 (EEB + basic calibration)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--predictions", required=True, help="JSON predictions list (engine output)")
    p.add_argument("--a2-phase", required=False, help="A2 phase artifact to annotate terms")
    p.add_argument("--out-reports", default="out/reports")
    args = p.parse_args()

    ts = _utc_now_iso()
    pred = _read_json(args.predictions)
    items = pred.get("predictions") or pred.get("items") or []
    if not isinstance(items, list):
        items = []

    phase_map: Dict[str, Dict[str, Any]] = {}
    if args.a2_phase:
        a2_phase = _read_json(args.a2_phase)
        profiles = a2_phase.get("profiles") or []
        if isinstance(profiles, list):
            for profile in profiles:
                if isinstance(profile, dict) and profile.get("term"):
                    phase_map[str(profile["term"]).lower()] = profile

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

        eeb = expected_error_band(
            horizon=horizon,
            phase=phase,
            half_life_days=half_life,
            manipulation_risk=risk,
            recurrence_days=recurrence if recurrence is None else float(recurrence),
        )
        out_item = {
            **item,
            "phase": phase,
            "half_life_days_fit": half_life,
            "manipulation_risk_mean": risk,
            "expected_error_band": eeb.to_dict(),
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
        "views": {"annotated_top_30": annotated[:30]},
        "provenance": {"builder": "abx.forecast_score.v0.1"},
    }
    out = enforce_non_truncation(
        artifact=out_core,
        raw_full={"annotated": list(annotated)},
    )

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
