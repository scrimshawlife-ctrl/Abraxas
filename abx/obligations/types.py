from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalCommitmentRecord:
    commitment_id: str
    counterparty: str
    scope_ref: str
    authority: str
    commitment_state: str


@dataclass(frozen=True)
class DeadlineRecord:
    deadline_id: str
    commitment_id: str
    deadline_kind: str
    due_date: str
    due_window: str


@dataclass(frozen=True)
class DueStateRecord:
    due_state_id: str
    deadline_id: str
    due_state: str
    risk_state: str


@dataclass(frozen=True)
class ObligationLifecycleRecord:
    lifecycle_id: str
    commitment_id: str
    lifecycle_state: str
    owner: str
    blocker_ref: str


@dataclass(frozen=True)
class DischargeEvidenceRecord:
    evidence_id: str
    commitment_id: str
    discharge_state: str
    evidence_ref: str


@dataclass(frozen=True)
class ObligationTransitionRecord:
    transition_id: str
    commitment_id: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class SupersededObligationRecord:
    supersession_id: str
    commitment_id: str
    superseded_by: str
    reason: str


@dataclass(frozen=True)
class CanceledObligationRecord:
    cancellation_id: str
    commitment_id: str
    cancellation_state: str
    reason: str


@dataclass(frozen=True)
class ObligationGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ObligationGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
