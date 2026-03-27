from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceThresholdRecord:
    threshold_id: str
    decision_class: str
    consequence_level: str
    reversibility: str
    threshold_rule: str
    threshold_value: float


@dataclass(frozen=True)
class BurdenOfProofRecord:
    burden_id: str
    decision_class: str
    burden_owner: str
    burden_standard: str
    evidence_strength: float


@dataclass(frozen=True)
class DecisionSufficiencyRecord:
    sufficiency_id: str
    decision_class: str
    sufficiency_state: str
    rationale_ref: str


@dataclass(frozen=True)
class DecisionReadinessRecord:
    readiness_id: str
    decision_class: str
    readiness_state: str
    readiness_reason: str


@dataclass(frozen=True)
class ConflictingEvidenceRecord:
    conflict_id: str
    decision_class: str
    conflict_state: str
    evidence_refs: tuple[str, str]


@dataclass(frozen=True)
class ProvisionalDecisionRecord:
    provisional_id: str
    decision_class: str
    provisional_state: str
    review_by: str


@dataclass(frozen=True)
class EvidenceTransitionRecord:
    transition_id: str
    decision_class: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class UnmetBurdenRecord:
    unmet_id: str
    decision_class: str
    unmet_state: str
    detail: str


@dataclass(frozen=True)
class EvidenceGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class EvidenceGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
