from __future__ import annotations

from abx.epistemics.qualityClassification import classify_epistemic_quality_states
from abx.epistemics.types import EpistemicCoverageRecord


def build_epistemic_coverage() -> list[EpistemicCoverageRecord]:
    quality = classify_epistemic_quality_states()
    return [
        EpistemicCoverageRecord(
            coverage_id="coverage.validation",
            dimension="validation_surface_coverage",
            status="governed",
            evidence_refs=quality["VERIFIED"] + quality["MONITORED"],
        ),
        EpistemicCoverageRecord(
            coverage_id="coverage.uncertainty",
            dimension="uncertainty_visibility",
            status="partial" if quality["NOT_COMPUTABLE"] else "governed",
            evidence_refs=quality["SUSPECT"] + quality["NOT_COMPUTABLE"],
        ),
    ]
