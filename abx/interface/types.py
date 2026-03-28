from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterfaceContractRecord:
    contract_id: str
    boundary_ref: str
    contract_state: str
    integrity_surface: str


@dataclass(frozen=True)
class HandoffStateRecord:
    handoff_id: str
    boundary_ref: str
    handoff_state: str
    transport_state: str


@dataclass(frozen=True)
class DeliveryRecord:
    delivery_id: str
    handoff_ref: str
    delivery_state: str
    delivery_reason: str


@dataclass(frozen=True)
class AcceptanceRecord:
    acceptance_id: str
    handoff_ref: str
    acceptance_state: str
    acceptance_reason: str


@dataclass(frozen=True)
class InterpretationRecord:
    interpretation_id: str
    handoff_ref: str
    interpretation_state: str
    interpretation_reason: str


@dataclass(frozen=True)
class CrossBoundaryMismatchRecord:
    mismatch_id: str
    handoff_ref: str
    mismatch_state: str
    mismatch_reason: str


@dataclass(frozen=True)
class DegradedHandoffRecord:
    degraded_id: str
    handoff_ref: str
    degraded_state: str
    degraded_reason: str


@dataclass(frozen=True)
class DeliveryTransitionRecord:
    transition_id: str
    handoff_ref: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class InterfaceGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class CrossBoundaryDeliveryScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
