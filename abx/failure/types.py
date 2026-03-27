from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorTaxonomyRecord:
    error_id: str
    subsystem: str
    source_type: str
    severity: str
    failure_class: str


@dataclass(frozen=True)
class FailureSemanticRecord:
    semantic_id: str
    error_id: str
    recoverability: str
    degraded_state: str
    integrity_impact: str


@dataclass(frozen=True)
class RecoverabilityRecord:
    recoverability_id: str
    semantic_id: str
    retryability: str
    human_intervention: str


@dataclass(frozen=True)
class RecoveryEligibilityRecord:
    eligibility_id: str
    error_id: str
    retry_allowed: str
    restore_allowed: str
    clearance_required: str


@dataclass(frozen=True)
class IntegrityRiskRecord:
    integrity_id: str
    error_id: str
    integrity_state: str


@dataclass(frozen=True)
class RecoveryActionRecord:
    action_id: str
    error_id: str
    action_state: str
    action_reason: str


@dataclass(frozen=True)
class FailureTransitionRecord:
    transition_id: str
    error_id: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class UnsafeRestorationRecord:
    unsafe_id: str
    error_id: str
    unsafe_state: str
    block_reason: str


@dataclass(frozen=True)
class FailureGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class FailureGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
