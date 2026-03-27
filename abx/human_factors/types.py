from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InteractionSurfaceRecord:
    surface_id: str
    task_type: str
    workflow_phase: str
    condition_scope: str
    surface_class: str
    owner: str
    expertise_level: str


@dataclass(frozen=True)
class CognitivePriorityRecord:
    priority_id: str
    signal_type: str
    salience: str
    urgency: str
    action_window: str
    owner: str


@dataclass(frozen=True)
class WarningRecord:
    warning_id: str
    warning_class: str
    salience: str
    evidence_ref: str
    next_action: str
    drilldown_surface: str


@dataclass(frozen=True)
class SummarySurfaceRecord:
    summary_id: str
    summary_class: str
    layer: str
    canonical_source: str
    redundancy_status: str


@dataclass(frozen=True)
class ActionSurfaceRecord:
    action_id: str
    action_class: str
    entry_surface: str
    authority_ref: str
    defer_safe: bool


@dataclass(frozen=True)
class OperatorPathRecord:
    path_id: str
    condition: str
    start_surface: str
    next_surface: str
    path_state: str
    recovery_link: str


@dataclass(frozen=True)
class CognitiveLoadRecord:
    load_id: str
    surface_id: str
    load_class: str
    mode_switches: int
    overload_risk: str


@dataclass(frozen=True)
class HumanFactorsCoverageRecord:
    coverage_id: str
    dimension: str
    status: str
    evidence_refs: list[str]


@dataclass(frozen=True)
class HumanFactorsGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class UXHumanFactorsScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
