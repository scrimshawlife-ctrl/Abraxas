from __future__ import annotations

from abx.epistemics.calibrationRecords import build_calibration_records
from abx.epistemics.types import ConfidenceClassificationRecord


def build_confidence_classification_records() -> list[ConfidenceClassificationRecord]:
    records: list[ConfidenceClassificationRecord] = []
    for row in build_calibration_records():
        support = "supported" if row.calibration_status == "calibrated" else "heuristic"
        if row.calibration_status == "unsupported_confidence":
            support = "unsupported"
        if row.calibration_status == "not_computable":
            support = "not_computable"
        records.append(
            ConfidenceClassificationRecord(
                record_id=f"conf.{row.calibration_id}",
                output_surface=row.output_surface,
                confidence_state=row.calibration_status,
                support_state=support,
                consequence_scope="decision_support",
            )
        )
    return records


def classify_confidence_states() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "calibrated": [],
        "bounded_heuristic": [],
        "unsupported_confidence": [],
        "uncertainty_without_confidence": [],
        "not_computable": [],
    }
    for row in build_confidence_classification_records():
        key = row.confidence_state
        out[key].append(row.record_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_unsupported_confidence_drift() -> list[str]:
    return sorted(
        x.record_id for x in build_confidence_classification_records() if x.support_state == "unsupported"
    )
