from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeSurfaceRecord:
    surface_id: str
    classification: str
    owner: str
    influences_runtime: bool


@dataclass(frozen=True)
class ActiveVsHistoricalClassificationRecord:
    surface_id: str
    activity_state: str


@dataclass(frozen=True)
class MemoryLifecycleRecord:
    memory_id: str
    lifecycle_state: str
    permitted_usage: str


@dataclass(frozen=True)
class MemoryRetentionRecord:
    memory_id: str
    retention_rule: str
    expires_after: str


@dataclass(frozen=True)
class ContinuityRecord:
    continuity_id: str
    run_id: str
    previous_ref: str | None
    baseline_ref: str | None
    incident_ref: str | None
    linkage_type: str


@dataclass(frozen=True)
class ContinuityCoverageRecord:
    run_id: str
    complete: bool
    missing_links: list[str]


@dataclass(frozen=True)
class CarryForwardPolicyRecord:
    policy_id: str
    state: str
    eligible_surfaces: list[str]
    prohibited_surfaces: list[str]


@dataclass(frozen=True)
class ForgettingPolicyRecord:
    policy_id: str
    expiry_states: list[str]
    archival_only_states: list[str]


@dataclass(frozen=True)
class MemoryGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class KnowledgeContinuityScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
