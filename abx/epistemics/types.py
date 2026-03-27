from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationSurfaceRecord:
    validation_id: str
    workflow: str
    capability: str
    validation_kind: str
    trust_level: str
    owner: str


@dataclass(frozen=True)
class CalibrationRecord:
    calibration_id: str
    output_surface: str
    evidence_strength: str
    calibration_status: str
    confidence_band: str
    owner: str


@dataclass(frozen=True)
class ConfidenceClassificationRecord:
    record_id: str
    output_surface: str
    confidence_state: str
    support_state: str
    consequence_scope: str


@dataclass(frozen=True)
class EpistemicQualityRecord:
    quality_id: str
    target_surface: str
    quality_state: str
    evidence_linkage: str
    validation_linkage: str
    alignment_linkage: str


@dataclass(frozen=True)
class AlignmentRecord:
    alignment_id: str
    live_surface: str
    reference_surface: str
    alignment_class: str
    status: str


@dataclass(frozen=True)
class GroundTruthReferenceRecord:
    reference_id: str
    reference_surface: str
    reference_class: str
    reliability: str
    owner: str


@dataclass(frozen=True)
class ReplayComparisonRecord:
    comparison_id: str
    replay_surface: str
    live_surface: str
    mismatch_class: str
    status: str


@dataclass(frozen=True)
class EpistemicCoverageRecord:
    coverage_id: str
    dimension: str
    status: str
    evidence_refs: list[str]


@dataclass(frozen=True)
class EpistemicGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class EpistemicQualityScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
