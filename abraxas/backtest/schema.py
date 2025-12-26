"""
Backtest Schema — Pydantic Models

Defines data structures for backtest cases, triggers, and results.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BacktestStatus(str, Enum):
    """Backtest evaluation status."""

    HIT = "HIT"  # Forecast correctly predicted outcome
    MISS = "MISS"  # Forecast did not match outcome
    ABSTAIN = "ABSTAIN"  # Insufficient evidence to evaluate
    UNKNOWN = "UNKNOWN"  # Required data missing


class Confidence(str, Enum):
    """Confidence level in backtest result."""

    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


class TriggerKind(str, Enum):
    """Types of triggers."""

    TERM_SEEN = "term_seen"
    MW_SHIFT = "mw_shift"
    TAU_SHIFT = "tau_shift"
    INTEGRITY_VECTOR = "integrity_vector"
    INDEX_THRESHOLD = "index_threshold"


class TriggerSpec(BaseModel):
    """Specification for a single trigger condition."""

    kind: TriggerKind
    params: Dict[str, Any] = Field(default_factory=dict)


class ForecastRef(BaseModel):
    """Reference to forecast artifact."""

    run_id: str
    artifact_path: str
    tier: str = Field(..., pattern="^(psychonaut|analyst|enterprise)$")


class EvaluationWindow(BaseModel):
    """Time window for backtest evaluation."""

    start_ts: datetime
    end_ts: datetime


class Triggers(BaseModel):
    """Collection of trigger specifications."""

    any_of: List[TriggerSpec] = Field(default_factory=list)
    all_of: List[TriggerSpec] = Field(default_factory=list)


class Guardrails(BaseModel):
    """Guardrails to prevent false confidence."""

    min_signal_count: int = 0
    min_evidence_completeness: float = 0.0
    max_integrity_risk: float = 1.0


class Scoring(BaseModel):
    """Scoring configuration."""

    type: str = Field(..., pattern="^(binary|graded)$")
    weights: Dict[str, float] = Field(default_factory=dict)


class Provenance(BaseModel):
    """Provenance metadata for backtest case."""

    required_ledgers: List[str] = Field(default_factory=list)
    required_sources: List[str] = Field(default_factory=list)
    smem_version: Optional[str] = None
    siw_version: Optional[str] = None


class BacktestCase(BaseModel):
    """Complete backtest case specification."""

    case_id: str
    created_at: datetime
    description: str
    forecast_ref: ForecastRef
    evaluation_window: EvaluationWindow
    triggers: Triggers
    falsifiers: Triggers = Field(default_factory=lambda: Triggers())
    guardrails: Guardrails = Field(default_factory=Guardrails)
    scoring: Scoring
    provenance: Provenance = Field(default_factory=Provenance)


class TriggerResult(BaseModel):
    """Result of evaluating a single trigger."""

    trigger_kind: TriggerKind
    satisfied: bool
    match_count: int = 0
    notes: List[str] = Field(default_factory=list)


class BacktestResult(BaseModel):
    """Result of evaluating a backtest case."""

    case_id: str
    status: BacktestStatus
    score: float
    confidence: Confidence
    satisfied_triggers: List[str] = Field(default_factory=list)
    satisfied_falsifiers: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
