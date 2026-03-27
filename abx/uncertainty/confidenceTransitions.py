from __future__ import annotations

from abx.uncertainty.types import ConfidenceTransitionRecord


def build_confidence_transition_records() -> tuple[ConfidenceTransitionRecord, ...]:
    return (
        ConfidenceTransitionRecord("ctr.001", "CLASSIFICATION", "NUMERIC", "SUPPRESSED", "miscalibration_detected"),
        ConfidenceTransitionRecord("ctr.002", "FORECAST", "INTERVAL", "QUALITATIVE", "stale_calibration"),
        ConfidenceTransitionRecord("ctr.003", "RECOMMENDATION", "SUPPRESSED", "ABSTAIN_FROM_CONFIDENCE", "insufficient_reliability"),
        ConfidenceTransitionRecord("ctr.004", "RANKING", "QUALITATIVE", "NUMERIC", "recalibration_complete"),
    )
