from __future__ import annotations


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def normalize_prediction(payload: dict) -> dict | None:
    required = ["prediction_id", "event_id", "predicted_outcome", "probability"]
    if any(field not in payload for field in required):
        return None
    return {
        "prediction_id": str(payload["prediction_id"]),
        "event_id": str(payload["event_id"]),
        "predicted_outcome": str(payload["predicted_outcome"]),
        "probability": clamp01(payload["probability"]),
    }


def normalize_outcome(payload: dict) -> dict | None:
    required = ["event_id", "resolved_outcome"]
    if any(field not in payload for field in required):
        return None
    return {
        "event_id": str(payload["event_id"]),
        "resolved_outcome": str(payload["resolved_outcome"]),
    }
