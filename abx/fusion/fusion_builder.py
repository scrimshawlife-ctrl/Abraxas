from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from abx.schemas.cross_domain_fusion_projection import CrossDomainFusionProjection

_STATUS_SIGNAL = {
    "PASS": 1.0,
    "REVIEW_REQUIRED": 0.7,
    "FAIL": 0.4,
    "NOT_COMPUTABLE": 0.0,
}


def build_fusion_projection(
    report: Mapping[str, Any],
    advisory: Mapping[str, Any],
) -> CrossDomainFusionProjection:
    drift_status = str(report.get("calibration_drift_status", "NOT_COMPUTABLE") or "NOT_COMPUTABLE")
    signal = _STATUS_SIGNAL.get(drift_status, 0.0)

    adjusted_weights_raw = advisory.get("adjusted_weights", {})
    adjusted_weights = adjusted_weights_raw if isinstance(adjusted_weights_raw, dict) else {}
    domain_pressure_vector = {
        str(domain): float(weight) * signal
        for domain, weight in sorted(adjusted_weights.items(), key=lambda item: str(item[0]))
    }

    fused_priority_score = float(sum(domain_pressure_vector.values()))

    dominant_domain = "NOT_COMPUTABLE"
    dominance_ratio = 0.0
    if domain_pressure_vector:
        dominant_domain = max(domain_pressure_vector, key=domain_pressure_vector.get)
        sorted_vals = sorted(domain_pressure_vector.values(), reverse=True)
        if len(sorted_vals) >= 2 and sorted_vals[1] > 0:
            dominance_ratio = domain_pressure_vector[dominant_domain] / sorted_vals[1]
        elif sorted_vals and sorted_vals[0] > 0:
            dominance_ratio = float("inf")

    drift_alerts: list[str] = []
    if drift_status != "PASS":
        drift_alerts.append("CALIBRATION_DRIFT")
    if dominance_ratio > 1.5:
        drift_alerts.append("DOMAIN_DOMINANCE_DRIFT")
    confidence = float(advisory.get("confidence", 0.0) or 0.0)
    if confidence < 0.5:
        drift_alerts.append("LOW_CONFIDENCE")

    return {
        "schema_version": "CrossDomainFusionProjection.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "calibration_ref": str(report.get("schema_version", "CalibrationDriftReport.v1")),
        "advisory_ref": str(advisory.get("schema_version", "DomainWeightAdvisory.v1")),
        "fused_priority_score": fused_priority_score,
        "domain_pressure_vector": domain_pressure_vector,
        "dominant_domain": dominant_domain,
        "dominance_ratio": dominance_ratio,
        "drift_alerts": drift_alerts,
        "authority_effect": "ADVISORY_ONLY",
        "confidence": confidence,
        "evidence_refs": [
            "abx.calibration.report_builder.build_calibration_report",
            "abx.weighting.advisory_builder.build_domain_weight_advisory",
            "abx.fusion.fusion_builder._STATUS_SIGNAL",
        ],
    }
