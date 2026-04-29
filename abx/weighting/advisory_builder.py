from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from abx.schemas.domain_weight_advisory import DomainWeightAdvisory

DEFAULT_WEIGHTS: dict[str, float] = {
    "market_pse": 0.35,
    "oracle": 0.25,
    "coding": 0.20,
    "memetic": 0.20,
}


def _normalize(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    ordered = sorted(weights.keys())
    normalized = {k: weights[k] / total for k in ordered}
    return normalized




def _confidence_from_report(report: Mapping[str, Any]) -> float:
    status = str(report.get("calibration_drift_status", "NOT_COMPUTABLE") or "NOT_COMPUTABLE")
    if status == "NOT_COMPUTABLE":
        return 0.0
    mean_brier = report.get("mean_brier")
    sample_size = report.get("sample_size", 0)
    if mean_brier is None or float(sample_size) <= 0:
        return 0.0
    base_by_status = {
        "PASS": 1.0,
        "REVIEW_REQUIRED": 0.65,
        "FAIL": 0.25,
        "NOT_COMPUTABLE": 0.0,
    }
    base = float(base_by_status.get(status, 0.0))
    brier_penalty = min(float(mean_brier) * 2.0, 1.0)
    sample_factor = min(float(sample_size) / 10.0, 1.0)
    confidence = base * (1.0 - brier_penalty) * sample_factor
    return max(0.0, min(1.0, round(confidence, 6)))


def build_domain_weight_advisory(report: Mapping[str, Any]) -> DomainWeightAdvisory:
    drift_status = str(report.get("calibration_drift_status", "NOT_COMPUTABLE") or "NOT_COMPUTABLE")
    base_weights = dict(DEFAULT_WEIGHTS)
    dominant_domain = max(base_weights, key=base_weights.get)
    adjusted = dict(base_weights)

    if drift_status == "PASS":
        adjustment_reason = "CALIBRATION_PASS"
        confidence = _confidence_from_report(report)
    elif drift_status == "REVIEW_REQUIRED":
        adjustment_reason = "CALIBRATION_REVIEW_REQUIRED"
        confidence = _confidence_from_report(report)
        delta = 0.03
        adjusted[dominant_domain] = max(0.0, adjusted[dominant_domain] - delta)
        spread = delta / float(len(adjusted) - 1)
        for domain in sorted(adjusted.keys()):
            if domain != dominant_domain:
                adjusted[domain] += spread
    elif drift_status == "FAIL":
        adjustment_reason = "CALIBRATION_FAIL"
        confidence = _confidence_from_report(report)
        delta = 0.07
        adjusted[dominant_domain] = max(0.0, adjusted[dominant_domain] - delta)
        spread = delta / float(len(adjusted) - 1)
        for domain in sorted(adjusted.keys()):
            if domain != dominant_domain:
                adjusted[domain] += spread
    else:
        adjustment_reason = "NOT_COMPUTABLE"
        confidence = 0.0

    adjusted_weights = _normalize(adjusted)
    drift_detected = drift_status in {"REVIEW_REQUIRED", "FAIL"}
    input_ref = str(report.get("schema_version", "CalibrationDriftReport.v1"))

    return {
        "schema_version": "DomainWeightAdvisory.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_ref": input_ref,
        "base_weights": base_weights,
        "adjusted_weights": adjusted_weights,
        "adjustment_reason": adjustment_reason,
        "confidence": confidence,
        "dominant_domain": dominant_domain,
        "drift_detected": drift_detected,
        "evidence_refs": [
            "abx.weighting.advisory_builder.DEFAULT_WEIGHTS",
            "abx.calibration.report_builder.build_calibration_report",
        ],
        "advisory_only": True,
    }
