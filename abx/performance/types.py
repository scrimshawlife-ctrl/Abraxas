from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceSurfaceRecord:
    surface_id: str
    workflow: str
    capability: str
    environment_scope: str
    criticality: str
    cost_class: str
    owner: str


@dataclass(frozen=True)
class ResourceAccountingRecord:
    record_id: str
    workflow: str
    capability: str
    resource_type: str
    attribution_owner: str
    accounting_mode: str
    necessity_class: str
    unit: str
    value: float


@dataclass(frozen=True)
class LatencyVisibilityRecord:
    record_id: str
    surface_id: str
    latency_class: str
    source_kind: str
    controllability: str
    status: str


@dataclass(frozen=True)
class ThroughputConstraintRecord:
    record_id: str
    surface_id: str
    constraint_type: str
    scope: str
    status: str
    evidence: str


@dataclass(frozen=True)
class OverheadAttributionRecord:
    record_id: str
    surface_id: str
    overhead_type: str
    ownership: str
    avoidability: str
    accounting_mode: str


@dataclass(frozen=True)
class BudgetRecord:
    budget_id: str
    scope: str
    owner: str
    class_name: str
    limit_kind: str
    value: float
    unit: str


@dataclass(frozen=True)
class QuotaRecord:
    quota_id: str
    scope: str
    owner: str
    limit_kind: str
    value: float
    unit: str


@dataclass(frozen=True)
class ThrottleRecord:
    throttle_id: str
    scope: str
    owner: str
    throttle_class: str
    trigger: str
    action: str
    precedence: int


@dataclass(frozen=True)
class PerformanceGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class PerformanceResourceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
