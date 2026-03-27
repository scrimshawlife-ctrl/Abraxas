from __future__ import annotations

from abx.uncertainty.types import CalibrationValidityRecord


def build_calibration_inventory() -> tuple[CalibrationValidityRecord, ...]:
    return (
        CalibrationValidityRecord("cal.forecast", "FORECAST", 0.74, "PROVISIONALLY_CALIBRATED"),
        CalibrationValidityRecord("cal.classifier", "CLASSIFICATION", 0.51, "UNCALIBRATED"),
        CalibrationValidityRecord("cal.recommend", "RECOMMENDATION", 0.45, "RECALIBRATION_REQUIRED"),
        CalibrationValidityRecord("cal.ranking", "RANKING", 0.86, "CALIBRATED"),
        CalibrationValidityRecord("cal.anomaly", "ANOMALY_ALERT", 0.62, "PARTIALLY_CALIBRATED"),
    )
