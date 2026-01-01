"""Data models for OAS (Operator Auto-Synthesis)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef


class OperatorStatus(str, Enum):
    """Status of an operator in the lifecycle."""

    STAGING = "staging"
    CANONICAL = "canonical"
    LEGACY = "legacy"
    DEPRECATED = "deprecated"


class OperatorCandidate(BaseModel):
    """A candidate operator discovered by OAS."""

    operator_id: str = Field(..., description="Unique operator identifier")
    label: str = Field(..., description="Human-readable label")
    class_tags: list[str] = Field(default_factory=list, description="Classification tags")
    triggers: list[str] = Field(
        default_factory=list, description="Trigger patterns or conditions"
    )
    readouts: list[str] = Field(
        default_factory=list, description="Possible readout labels"
    )
    failure_modes: list[str] = Field(
        default_factory=list, description="Known failure modes"
    )
    scope: dict[str, Any] = Field(
        default_factory=dict, description="Scope metadata (languages, domains, etc.)"
    )
    tests: list[str] = Field(
        default_factory=list, description="Test cases or validation criteria"
    )
    provenance: ProvenanceBundle = Field(..., description="Full provenance record")
    discovery_window: dict[str, Any] = Field(
        ..., description="Discovery time window and sources"
    )
    evidence_hashes: list[str] = Field(
        default_factory=list, description="Hashes of input frames used as evidence"
    )
    candidate_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Quality/confidence score"
    )
    version: str = Field(default="1.0.0", description="Candidate version")
    status: OperatorStatus = Field(
        default=OperatorStatus.STAGING, description="Current status"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ValidationReport(BaseModel):
    """Report from validation phase."""

    passed: bool = Field(..., description="Whether validation passed")
    metrics_before: dict[str, float] = Field(
        default_factory=dict, description="Metrics before operator"
    )
    metrics_after: dict[str, float] = Field(
        default_factory=dict, description="Metrics after operator"
    )
    deltas: dict[str, float] = Field(
        default_factory=dict, description="Metric deltas (after - before)"
    )
    notes: list[str] = Field(default_factory=list, description="Validation notes")
    provenance: ProvenanceBundle = Field(..., description="Validation provenance")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Validation timestamp",
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class StabilizationState(BaseModel):
    """State tracking for stabilization phase."""

    operator_id: str = Field(..., description="Operator being stabilized")
    cycles_required: int = Field(default=3, ge=1, description="Required stabilization cycles")
    cycles_completed: int = Field(default=0, ge=0, description="Completed cycles")
    last_reports: list[ValidationReport] = Field(
        default_factory=list, description="Recent validation reports"
    )
    stable: bool = Field(default=False, description="Whether operator is stable")
    notes: list[str] = Field(default_factory=list, description="Stabilization notes")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Stabilization start time",
    )
    completed_at: datetime | None = Field(
        default=None, description="Stabilization completion time"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CanonDecision(BaseModel):
    """Decision record for canonization."""

    adopted: bool = Field(..., description="Whether operator was adopted as canonical")
    reason: str = Field(..., description="Reason for decision")
    operator_id: str = Field(..., description="Operator ID")
    version: str = Field(..., description="Operator version")
    ledger_ref: ProvenanceRef = Field(..., description="Reference to ledger entry")
    metrics_delta: dict[str, float] = Field(
        default_factory=dict, description="Final metrics improvement"
    )
    provenance: ProvenanceBundle = Field(..., description="Decision provenance")
    decided_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Decision timestamp",
    )
    decided_by: str = Field(default="oasis_canonizer", description="Decision maker")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
