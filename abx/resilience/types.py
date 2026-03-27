from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResilienceEvidence:
    evidence_id: str
    source: str
    detail: str


@dataclass(frozen=True)
class FaultInjectionArtifact:
    artifact_type: str
    artifact_id: str
    scenario_id: str
    injection_plan: list[dict[str, str]]
    injected_domains: list[str]
    status: str
    evidence: list[ResilienceEvidence]
    injection_hash: str


@dataclass(frozen=True)
class RecoveryDrillArtifact:
    artifact_type: str
    artifact_id: str
    drill_id: str
    scenario_id: str
    mode: str
    runbook_id: str
    expected_outcomes: list[str]
    actual_outcomes: list[str]
    comparison: dict[str, str]
    status: str
    drill_hash: str


@dataclass(frozen=True)
class DegradationStateRecord:
    artifact_type: str
    artifact_id: str
    scenario_id: str
    subsystem: str
    state: str
    fallback_actions: list[str]
    emitted_artifacts: list[str]
    rationale: str
    state_hash: str


@dataclass(frozen=True)
class TrainingScenarioArtifact:
    artifact_type: str
    artifact_id: str
    scenario_id: str
    drill_id: str
    guided_steps: list[str]
    expected_outputs: list[str]
    observed_outputs: list[str]
    evaluation_summary: dict[str, Any]
    training_hash: str


@dataclass(frozen=True)
class ResilienceScorecard:
    artifact_type: str
    artifact_id: str
    scenario_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
