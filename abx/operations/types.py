from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    command: str
    expected_artifact: str
    on_failure: str


@dataclass(frozen=True)
class RunbookArtifact:
    artifact_type: str
    artifact_id: str
    runbook_id: str
    category: str
    preflight: list[str]
    steps: list[WorkflowStep]
    completion_checks: list[str]
    runbook_hash: str


@dataclass(frozen=True)
class RunbookExecutionSummary:
    artifact_type: str
    artifact_id: str
    runbook_id: str
    status: str
    executed_steps: list[str]
    expected_outputs: list[str]
    summary_hash: str


@dataclass(frozen=True)
class IncidentRecord:
    incident_id: str
    category: str
    severity: str
    affected_surfaces: list[str]
    evidence_refs: list[str]
    rollback_possible: bool


@dataclass(frozen=True)
class IncidentSummaryArtifact:
    artifact_type: str
    artifact_id: str
    incidents: list[dict[str, Any]]
    summary_hash: str


@dataclass(frozen=True)
class RollbackPlanArtifact:
    artifact_type: str
    artifact_id: str
    incident_id: str
    strategy: str
    pre_validation: list[str]
    rollback_steps: list[WorkflowStep]
    post_validation: list[str]
    rollback_hash: str


@dataclass(frozen=True)
class RollbackExecutionSummary:
    artifact_type: str
    artifact_id: str
    incident_id: str
    status: str
    executed_steps: list[str]
    summary_hash: str


@dataclass(frozen=True)
class FailureDomainRecord:
    domain_id: str
    domain_group: str
    severity: str
    affected_surfaces: list[str]
    evidence_surfaces: list[str]
    response_runbook: str


@dataclass(frozen=True)
class ServiceExpectationRecord:
    subsystem: str
    expectation: str
    status: str
    breach_signal: str
    cadence: str


@dataclass(frozen=True)
class OperatingManualArtifact:
    artifact_type: str
    artifact_id: str
    baseline_id: str
    baseline_version: str
    sections: dict[str, Any]
    manual_hash: str
