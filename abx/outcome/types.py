from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntendedOutcomeRecord:
    outcome_id: str
    action_ref: str
    intended_state: str
    effect_surface: str


@dataclass(frozen=True)
class EffectRealizationRecord:
    realization_id: str
    action_ref: str
    realization_state: str
    evidence_mode: str


@dataclass(frozen=True)
class OutcomeVerificationRecord:
    verification_id: str
    action_ref: str
    verification_state: str
    verification_reason: str


@dataclass(frozen=True)
class PostActionTruthRecord:
    truth_id: str
    action_ref: str
    truth_state: str
    truth_reason: str


@dataclass(frozen=True)
class ContradictoryOutcomeRecord:
    contradiction_id: str
    action_ref: str
    contradiction_state: str
    contradiction_reason: str


@dataclass(frozen=True)
class OutcomeGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class OutcomeVerificationScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
