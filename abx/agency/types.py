from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AutonomousOperationRecord:
    operation_id: str
    surface_id: str
    mode: str
    authority_scope: str
    stop_conditions: list[str]
    status: str


@dataclass(frozen=True)
class ActionModeRecord:
    mode_id: str
    mode_class: str
    side_effect_class: str
    requires_confirmation: bool


@dataclass(frozen=True)
class DelegationRecord:
    delegation_id: str
    origin_actor: str
    delegate_actor: str
    handoff_type: str
    inherited_scope: str
    max_depth: int


@dataclass(frozen=True)
class DelegationChainRecord:
    chain_id: str
    origin_authority: str
    hops: list[str]
    depth: int
    recursion_state: str


@dataclass(frozen=True)
class GuardrailPolicyRecord:
    policy_id: str
    applies_to: list[str]
    policy_class: str
    enforcement_state: str
    ceiling: str


@dataclass(frozen=True)
class GuardrailTriggerRecord:
    trigger_id: str
    policy_id: str
    trigger_state: str
    reason: str


@dataclass(frozen=True)
class ActionBoundaryRecord:
    boundary_id: str
    surface_id: str
    transition_class: str
    side_effect_capability: str
    governance_state: str


@dataclass(frozen=True)
class SideEffectRecord:
    effect_id: str
    surface_id: str
    effect_class: str
    evidence_ref: str


@dataclass(frozen=True)
class HiddenChannelRecord:
    channel_id: str
    surface_id: str
    risk_class: str
    status: str
    reason: str


@dataclass(frozen=True)
class AgencyGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class AutonomousOperationScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
