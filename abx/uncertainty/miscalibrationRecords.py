from __future__ import annotations

from abx.uncertainty.types import ConfidenceSuppressionRecord, MiscalibrationRecord


def build_miscalibration_records() -> tuple[MiscalibrationRecord, ...]:
    return (
        MiscalibrationRecord("mis.classifier", "CLASSIFICATION", "MISCALIBRATED", "DRIFT_HIGH"),
        MiscalibrationRecord("mis.recommend", "RECOMMENDATION", "MISCALIBRATED", "DRIFT_MODERATE"),
    )


def build_confidence_suppression_records() -> tuple[ConfidenceSuppressionRecord, ...]:
    return (
        ConfidenceSuppressionRecord("sup.classifier", "CLASSIFICATION", "CONFIDENCE_SUPPRESSED", "invalid_calibration"),
        ConfidenceSuppressionRecord("sup.recommend", "RECOMMENDATION", "ABSTAIN_FROM_CONFIDENCE", "uncertainty_high"),
    )
