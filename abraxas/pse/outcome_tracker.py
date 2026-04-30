from __future__ import annotations

from abraxas.pse.models import normalize_outcome, normalize_prediction
from abraxas.pse.resolution import resolve_prediction


def _base_ledger() -> dict:
    return {
        "schema_version": "PSEOutcomeLedger.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "CANDIDATE_ONLY",
        "summary": {
            "total_predictions": 0,
            "resolved": 0,
            "unresolved": 0,
            "hits": 0,
            "misses": 0,
            "partial": 0,
            "not_computable": 0,
        },
        "resolutions": [],
        "diagnostics": [],
        "provenance": {"deterministic": True},
    }


def build_outcome_ledger(predictions: list[dict], outcomes: list[dict]) -> dict:
    ledger = _base_ledger()

    normalized_predictions = []
    for item in predictions:
        pred = normalize_prediction(item)
        if pred is None:
            return ledger
        normalized_predictions.append(pred)

    normalized_outcomes = []
    for item in outcomes:
        out = normalize_outcome(item)
        if out is None:
            return ledger
        normalized_outcomes.append(out)

    if not normalized_predictions:
        return ledger

    latest_outcomes: dict[str, dict] = {}
    for idx, out in enumerate(normalized_outcomes):
        latest_outcomes[out["event_id"]] = {"index": idx, **out}

    used_outcome_events = set()
    resolutions = []
    summary = ledger["summary"]

    for pred in sorted(normalized_predictions, key=lambda x: (x["event_id"], x["prediction_id"])):
        outcome = latest_outcomes.get(pred["event_id"])
        verdict = resolve_prediction(pred, outcome)
        if outcome is not None:
            used_outcome_events.add(pred["event_id"])

        summary["total_predictions"] += 1
        if verdict == "UNRESOLVED":
            summary["unresolved"] += 1
        else:
            summary["resolved"] += 1
        if verdict == "HIT":
            summary["hits"] += 1
        elif verdict == "MISS":
            summary["misses"] += 1
        elif verdict == "PARTIAL":
            summary["partial"] += 1
        elif verdict == "NOT_COMPUTABLE":
            summary["not_computable"] += 1

        resolutions.append(
            {
                "prediction_id": pred["prediction_id"],
                "event_id": pred["event_id"],
                "predicted_outcome": pred["predicted_outcome"],
                "probability": pred["probability"],
                "resolved_outcome": outcome["resolved_outcome"] if outcome else "UNRESOLVED",
                "resolution": verdict,
                "status": "RESOLVED" if verdict != "UNRESOLVED" else "UNRESOLVED",
            }
        )

    orphan_events = sorted(set(latest_outcomes.keys()) - used_outcome_events)
    for orphan in orphan_events:
        ledger["diagnostics"].append({"type": "ORPHAN_OUTCOME", "event_id": orphan})

    ledger["status"] = "CANDIDATE_ONLY"
    ledger["resolutions"] = resolutions
    return ledger
