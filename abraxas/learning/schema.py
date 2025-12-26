"""
Schema definitions for Active Learning Loops.

Pydantic models for failure analyses, proposals, sandbox reports, and promotions.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProposalType(str, Enum):
    """Type of proposal for improving backtest performance."""

    NEW_METRIC = "new_metric"
    NEW_OPERATOR = "new_operator"
    THRESHOLD_ADJUSTMENT = "threshold_adjustment"


class UnmetTrigger(BaseModel):
    """Details of a trigger that was not satisfied."""

    kind: str = Field(description="Trigger kind (e.g., term_seen, mw_shift)")
    expected: Dict[str, Any] = Field(description="Expected conditions")
    actual: Dict[str, Any] = Field(description="Actual observed values")


class SignalGaps(BaseModel):
    """Analysis of signal availability gaps."""

    missing_events: int = Field(description="Number of events below min_signal_count")
    denied_signals: int = Field(
        description="Number of signals filtered by SMEM/integrity"
    )
    missing_ledgers: List[str] = Field(
        default_factory=list, description="Ledgers that were not found"
    )


class IntegrityConditions(BaseModel):
    """Integrity metrics at time of evaluation."""

    max_ssi: float = Field(description="Maximum SSI (Synthetic Source Index) observed")
    synthetic_saturation: float = Field(
        description="Proportion of events flagged as synthetic"
    )


class TemporalGaps(BaseModel):
    """Temporal dynamics gaps."""

    tau_latency_mean: Optional[float] = Field(
        default=None, description="Mean τ latency in ms"
    )
    tau_phase_variance: Optional[float] = Field(
        default=None, description="τ phase variance"
    )


class FailureAnalysis(BaseModel):
    """
    Deterministic failure analysis artifact.

    Generated when backtest returns MISS or high-confidence ABSTAIN.
    Contains gap analysis without ML inference.
    """

    failure_id: str = Field(description="Unique failure identifier")
    case_id: str = Field(description="Backtest case ID")
    run_id: str = Field(description="Backtest run ID")

    backtest_result: Dict[str, Any] = Field(
        description="Backtest result details (status, score, confidence)"
    )

    unmet_triggers: List[UnmetTrigger] = Field(
        default_factory=list, description="Triggers that were not satisfied"
    )
    hit_falsifiers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Falsifiers that were triggered (causing MISS)",
    )

    signal_gaps: SignalGaps = Field(description="Analysis of signal availability")
    integrity_conditions: IntegrityConditions = Field(
        description="Integrity metrics at evaluation time"
    )
    temporal_gaps: TemporalGaps = Field(description="Temporal dynamics analysis")

    hypothesis: str = Field(
        description="Deterministic hypothesis about failure cause"
    )
    suggested_adjustments: List[str] = Field(
        default_factory=list,
        description="Potential adjustments to improve performance",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(), description="When analysis was created"
    )


class ExpectedDelta(BaseModel):
    """Expected impact of a proposal."""

    improved_cases: List[str] = Field(
        default_factory=list, description="Case IDs expected to improve"
    )
    regression_risk: List[str] = Field(
        default_factory=list, description="Case IDs at risk of regression"
    )
    backtest_pass_rate_delta: float = Field(
        description="Expected change in pass rate (e.g., +0.15)"
    )


class ValidationPlan(BaseModel):
    """Plan for sandbox validation of proposal."""

    sandbox_cases: List[str] = Field(
        description="Case IDs to test in sandbox (affected + protected)"
    )
    protected_cases: List[str] = Field(
        default_factory=list, description="Cases that must not regress"
    )
    stabilization_runs: int = Field(
        default=3, description="Number of consecutive runs required"
    )


class Proposal(BaseModel):
    """
    Bounded proposal for improving backtest performance.

    Exactly ONE proposal per failure analysis.
    """

    proposal_id: str = Field(description="Unique proposal identifier")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When proposal was created",
    )
    source_failure_id: str = Field(
        description="Failure ID that triggered this proposal"
    )

    proposal_type: ProposalType = Field(description="Type of proposal")
    change_description: str = Field(
        description="Human-readable description of proposed change"
    )

    affected_components: List[str] = Field(
        description="File paths or component IDs affected by this change"
    )

    expected_delta: ExpectedDelta = Field(
        description="Expected impact on backtest performance"
    )

    rent_manifest_draft: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Draft rent manifest if proposal is new_metric or new_operator",
    )

    validation_plan: ValidationPlan = Field(
        description="Plan for sandbox validation"
    )


class BaselineMetrics(BaseModel):
    """Baseline backtest metrics before proposal."""

    backtest_pass_rate: float = Field(description="Pass rate (HIT / total)")
    hit_count: int = Field(description="Number of HIT results")
    miss_count: int = Field(description="Number of MISS results")
    abstain_count: int = Field(description="Number of ABSTAIN results")
    avg_score: float = Field(description="Average score across all cases")


class ProposalMetrics(BaseModel):
    """Backtest metrics after applying proposal."""

    backtest_pass_rate: float = Field(description="Pass rate with proposal")
    hit_count: int = Field(description="Number of HIT results")
    miss_count: int = Field(description="Number of MISS results")
    abstain_count: int = Field(description="Number of ABSTAIN results")
    avg_score: float = Field(description="Average score across all cases")


class DeltaMetrics(BaseModel):
    """Delta between baseline and proposal."""

    pass_rate_delta: float = Field(description="Change in pass rate")
    hit_count_delta: int = Field(description="Change in HIT count")
    regression_count: int = Field(
        description="Number of previously-passing cases that now fail"
    )


class CostDelta(BaseModel):
    """Resource cost delta."""

    time_ms_delta: float = Field(description="Change in execution time (ms)")
    memory_kb_delta: float = Field(description="Change in memory usage (KB)")


class CaseDetail(BaseModel):
    """Per-case comparison."""

    case_id: str = Field(description="Case ID")
    baseline_status: str = Field(description="Status before proposal")
    proposal_status: str = Field(description="Status after proposal")
    improved: bool = Field(description="Whether this case improved")


class SandboxReport(BaseModel):
    """
    Sandbox execution report.

    Compares baseline vs proposal performance on historical data.
    """

    sandbox_run_id: str = Field(description="Unique sandbox run identifier")
    proposal_id: str = Field(description="Proposal being tested")
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(), description="When sandbox ran"
    )

    baseline: BaselineMetrics = Field(description="Baseline metrics")
    proposal: ProposalMetrics = Field(description="Proposal metrics")
    delta: DeltaMetrics = Field(description="Improvement delta")
    cost_delta: CostDelta = Field(description="Resource cost delta")

    case_details: List[CaseDetail] = Field(
        default_factory=list, description="Per-case breakdown"
    )

    promotion_eligible: bool = Field(
        description="Whether proposal meets promotion criteria"
    )


class ImprovementDelta(BaseModel):
    """Improvement metrics for promotion."""

    pass_rate_delta: float = Field(description="Change in pass rate")
    cost_delta: Dict[str, float] = Field(
        description="Resource cost changes (time_ms, memory_kb)"
    )


class PromotionEntry(BaseModel):
    """
    Ledger entry for promoted proposal.

    Records full provenance from failure → proposal → sandbox → promotion.
    """

    type: str = Field(default="promotion", description="Entry type")
    proposal_id: str = Field(description="Promoted proposal ID")
    source_failure_id: str = Field(description="Original failure that triggered this")

    promoted_at: datetime = Field(
        default_factory=lambda: datetime.now(), description="When promotion occurred"
    )

    improvement_delta: ImprovementDelta = Field(
        description="Measured improvement from sandbox"
    )
    provenance_note: str = Field(
        description="Human-readable provenance description"
    )

    ledger_sha256: str = Field(description="SHA256 of this entry")
