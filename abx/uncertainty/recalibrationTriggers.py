from __future__ import annotations

from abx.uncertainty.types import RecalibrationTriggerRecord


def build_recalibration_trigger_records() -> tuple[RecalibrationTriggerRecord, ...]:
    return (
        RecalibrationTriggerRecord("rt.classifier", "CLASSIFICATION", "RECALIBRATION_REQUIRED", "2026-04-05T00:00:00Z"),
        RecalibrationTriggerRecord("rt.recommend", "RECOMMENDATION", "RECALIBRATION_REQUIRED", "2026-04-01T00:00:00Z"),
        RecalibrationTriggerRecord("rt.ranking", "RANKING", "RECALIBRATION_COMPLETE", "2026-03-20T00:00:00Z"),
    )
