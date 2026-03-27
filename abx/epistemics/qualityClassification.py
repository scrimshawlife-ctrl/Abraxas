from __future__ import annotations

from abx.epistemics.confidenceClassification import build_confidence_classification_records
from abx.epistemics.types import EpistemicQualityRecord


QUALITY_STATES = (
    "VERIFIED",
    "GOVERNED_SUPPORTED",
    "MONITORED",
    "HEURISTIC",
    "DEGRADED",
    "SUSPECT",
    "UNKNOWN",
    "NOT_COMPUTABLE",
)


def build_epistemic_quality_records() -> list[EpistemicQualityRecord]:
    out: list[EpistemicQualityRecord] = []
    for row in build_confidence_classification_records():
        quality = "HEURISTIC"
        if row.confidence_state == "calibrated":
            quality = "VERIFIED"
        elif row.confidence_state == "bounded_heuristic":
            quality = "MONITORED"
        elif row.confidence_state == "unsupported_confidence":
            quality = "SUSPECT"
        elif row.confidence_state == "not_computable":
            quality = "NOT_COMPUTABLE"
        out.append(
            EpistemicQualityRecord(
                quality_id=f"quality.{row.record_id}",
                target_surface=row.output_surface,
                quality_state=quality,
                evidence_linkage=row.support_state,
                validation_linkage="linked_validation_surface",
                alignment_linkage="alignment_required",
            )
        )
    return out


def classify_epistemic_quality_states() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in QUALITY_STATES}
    for row in build_epistemic_quality_records():
        out[row.quality_state].append(row.quality_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_inconsistent_quality_terminology() -> list[str]:
    return sorted({x.quality_state for x in build_epistemic_quality_records() if x.quality_state not in QUALITY_STATES})
