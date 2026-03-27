from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UncertaintyRecord:
    uncertainty_id: str
    output_class: str
    uncertainty_type: str
    uncertainty_level: str
    downgrade_required: str


@dataclass(frozen=True)
class ConfidenceExpressionRecord:
    expression_id: str
    output_class: str
    expression_mode: str
    expression_value: str


@dataclass(frozen=True)
class CalibrationValidityRecord:
    calibration_id: str
    output_class: str
    reliability_score: float
    calibration_state: str


@dataclass(frozen=True)
class ConfidencePostureRecord:
    posture_id: str
    output_class: str
    confidence_posture: str
    reason: str


@dataclass(frozen=True)
class MiscalibrationRecord:
    miscalibration_id: str
    output_class: str
    miscalibration_state: str
    drift_state: str


@dataclass(frozen=True)
class ConfidenceSuppressionRecord:
    suppression_id: str
    output_class: str
    suppression_state: str
    reason: str


@dataclass(frozen=True)
class RecalibrationTriggerRecord:
    trigger_id: str
    output_class: str
    trigger_state: str
    due_by: str


@dataclass(frozen=True)
class ConfidenceTransitionRecord:
    transition_id: str
    output_class: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class UncertaintyGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class UncertaintyGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
