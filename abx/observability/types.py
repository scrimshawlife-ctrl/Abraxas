from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ObservabilitySurfaceRecord:
    surface_id: str
    source: str
    category: str
    status: str
    run_linkage: bool


@dataclass(frozen=True)
class ExplainIRArtifact:
    artifact_id: str
    explain_rune_id: str
    event_type: str
    observed: list[str]
    inferred: list[str]
    speculative: list[str]
    confidence: float


@dataclass(frozen=True)
class ProvenancePartitionRecord:
    artifact_id: str
    observed_count: int
    inferred_count: int
    speculative_count: int


@dataclass(frozen=True)
class ExplanationCoverageRecord:
    surface_id: str
    coverage_status: str
    owner: str


@dataclass(frozen=True)
class CausalTraceRecord:
    trace_id: str
    run_id: str
    step: str
    relation: str
    evidence_ref: str
    state: str


@dataclass(frozen=True)
class CausalTraceSummary:
    artifact_id: str
    run_id: str
    steps: list[str]
    degraded_points: list[str]
    summary_hash: str


@dataclass(frozen=True)
class TraceCoverageRecord:
    run_id: str
    traceable_surfaces: list[str]
    missing_surfaces: list[str]


@dataclass(frozen=True)
class OperatorInsightView:
    view_id: str
    run_id: str
    overview: dict[str, Any]
    drilldown: dict[str, Any]
    view_hash: str


@dataclass(frozen=True)
class ObservabilityErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ObservabilityHealthScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
