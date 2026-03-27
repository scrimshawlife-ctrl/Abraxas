from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LongHorizonPlanRecord:
    plan_id: str
    mission_id: str
    plan_state: str
    objective_thread: str
    horizon_class: str


@dataclass(frozen=True)
class PlanningHorizonRecord:
    horizon_id: str
    mission_id: str
    time_band: str
    checkpoint_policy: str
    viability_state: str


@dataclass(frozen=True)
class PersistedIntentRecord:
    intent_id: str
    mission_id: str
    persistence_state: str
    freshness_state: str
    revalidation_required: bool


@dataclass(frozen=True)
class MissionLifecycleRecord:
    lifecycle_id: str
    mission_id: str
    lifecycle_state: str
    evidence_ref: str
    changed_conditions: list[str]


@dataclass(frozen=True)
class ContinuityLineageRecord:
    lineage_id: str
    mission_id: str
    origin_mission_id: str
    branch_from: str
    supersedes: str


@dataclass(frozen=True)
class MissionTransitionRecord:
    transition_id: str
    mission_id: str
    from_state: str
    to_state: str
    transition_reason: str


@dataclass(frozen=True)
class SupersessionRecord:
    supersession_id: str
    mission_id: str
    superseded_by: str
    reason: str


@dataclass(frozen=True)
class RetirementRecord:
    retirement_id: str
    mission_id: str
    retirement_state: str
    archive_ref: str


@dataclass(frozen=True)
class ContinuityGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class MissionContinuityScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
