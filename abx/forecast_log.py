from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from abraxas.forecast.ledger import issue_prediction


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
    args = p.parse_args()

    forecast_score = _read_json(args.forecast_score)
    annotated = forecast_score.get("annotated") or []
    if not isinstance(annotated, list):
        annotated = []

    wrote = 0
    for item in annotated:
        if not isinstance(item, dict):
            continue
        term = str(item.get("term") or item.get("label") or "").strip()
        if not term:
            continue
        horizon = str(item.get("horizon") or "weeks")
        prob = float(item.get("p") or item.get("probability") or 0.5)
        issue_prediction(
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
            ledger_path=args.pred_ledger,
        )
        wrote += 1

    print(f"[FORECAST_LOG] appended {wrote} predictions → {args.pred_ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
