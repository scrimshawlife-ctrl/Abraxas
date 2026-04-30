from __future__ import annotations

from collections import defaultdict

from abraxas.pse.calibration_models import clamp01, scoreable_resolution


def _base() -> dict:
    return {
        "schema_version": "PSEBrierLedger.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "CANDIDATE_ONLY",
        "summary": {
            "scored_count": 0,
            "skipped_count": 0,
            "mean_brier": None,
            "best_brier": None,
            "worst_brier": None,
        },
        "scores": [],
        "by_domain": {},
        "by_source": {},
        "diagnostics": [],
        "provenance": {"deterministic": True},
    }


def build_brier_ledger(outcome_ledger: dict) -> dict:
    report = _base()
    resolutions = outcome_ledger.get("resolutions")
    if not isinstance(resolutions, list):
        return report

    scores = []
    by_domain = defaultdict(list)
    by_source = defaultdict(list)
    skipped = 0
    for item in sorted(resolutions, key=lambda x: (x.get("event_id", ""), x.get("prediction_id", ""))):
        if not scoreable_resolution(item):
            skipped += 1
            continue
        p = clamp01(item.get("probability", 0.0))
        forecast_probability = p if item["predicted_outcome"] == "YES" else 1.0 - p
        observed = 1.0 if item["predicted_outcome"] == item["resolved_outcome"] else 0.0
        brier = round((forecast_probability - observed) ** 2, 6)
        row = {
            "prediction_id": item.get("prediction_id", ""),
            "event_id": item.get("event_id", ""),
            "domain": item.get("domain", "unknown"),
            "source": item.get("source", "unknown"),
            "brier": brier,
        }
        scores.append(row)
        by_domain[row["domain"]].append(brier)
        by_source[row["source"]].append(brier)

    report["summary"]["skipped_count"] = skipped
    if not scores:
        return report

    values = [row["brier"] for row in scores]
    report["status"] = "CANDIDATE_ONLY"
    report["scores"] = scores
    report["summary"].update(
        {
            "scored_count": len(scores),
            "mean_brier": round(sum(values) / len(values), 6),
            "best_brier": min(values),
            "worst_brier": max(values),
        }
    )
    report["by_domain"] = {
        key: {"count": len(vals), "mean_brier": round(sum(vals) / len(vals), 6)}
        for key, vals in sorted(by_domain.items())
    }
    report["by_source"] = {
        key: {"count": len(vals), "mean_brier": round(sum(vals) / len(vals), 6)}
        for key, vals in sorted(by_source.items())
    }
    return report
