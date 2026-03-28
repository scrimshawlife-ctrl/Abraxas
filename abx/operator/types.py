from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HumanOverrideRecord:
    override_id: str
    surface: str
    requested_by: str
    authority_ref: str
    justification: str
    override_scope: str
    bypass_boundary: str
    requested_at: str
    expires_at: str
    status_signal: str


@dataclass(frozen=True)
class ManualInterventionRecord:
    intervention_id: str
    override_id: str
    intervention_kind_signal: str
    target_surface: str
    actor_id: str
    authority_ref: str
    effect_ref: str
    started_at: str
    ended_at: str


@dataclass(frozen=True)
class OverrideLegitimacyRecord:
    record_id: str
    override_id: str
    legitimacy: str
    reason: str


@dataclass(frozen=True)
class OperatorTraceRecord:
    trace_id: str
    intervention_id: str
    actor_id: str
    authority_ref: str
    reason_text: str
    scope_ref: str
    reversibility_signal: str
    restoration_ticket: str
    trace_state_signal: str


@dataclass(frozen=True)
class InterventionScopeRecord:
    scope_id: str
    intervention_id: str
    scope_state: str
    rationale: str


@dataclass(frozen=True)
class ReversibilityRecord:
    reversibility_id: str
    intervention_id: str
    reversibility_state: str
    restoration_required: str


@dataclass(frozen=True)
class OperatorTransitionRecord:
    transition_id: str
    intervention_id: str
    transition_kind: str
    from_state: str
    to_state: str
    occurred_at: str


@dataclass(frozen=True)
class ManualDriftRecord:
    drift_id: str
    intervention_id: str
    drift_state: str
    evidence_ref: str


@dataclass(frozen=True)
class OperatorGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class OperatorGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
