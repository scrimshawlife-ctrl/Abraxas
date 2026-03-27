from __future__ import annotations

from abx.epistemics.types import CalibrationRecord


def build_calibration_records() -> list[CalibrationRecord]:
    return [
        CalibrationRecord(
            calibration_id="cal.forecast.confidence_band",
            output_surface="forecast.outcome",
            evidence_strength="strong",
            calibration_status="calibrated",
            confidence_band="bounded_high",
            owner="forecast",
        ),
        CalibrationRecord(
            calibration_id="cal.trace.anomaly_severity",
            output_surface="observability.anomaly",
            evidence_strength="medium",
            calibration_status="bounded_heuristic",
            confidence_band="bounded_medium",
            owner="observability",
        ),
        CalibrationRecord(
            calibration_id="cal.adapter.semantic_mapping",
            output_surface="federation.adapter_mapping",
            evidence_strength="weak",
            calibration_status="unsupported_confidence",
            confidence_band="unbounded",
            owner="federation",
        ),
        CalibrationRecord(
            calibration_id="cal.legacy.import_quality",
            output_surface="legacy.import_bridge.direct_adapter",
            evidence_strength="unknown",
            calibration_status="not_computable",
            confidence_band="unknown",
            owner="integration",
        ),
    ]
