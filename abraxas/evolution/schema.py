"""
Evolution Schema — Candidate Types and Models

Defines data structures for metric evolution candidates, sandbox results,
and promotion tracking.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CandidateKind(str, Enum):
    """Types of evolution candidates."""

    METRIC = "metric"  # New metric (e.g., "term_coupling")
    OPERATOR = "operator"  # New SLANG operator (e.g., "semantic_distance")
    PARAM_TWEAK = "param_tweak"  # Parameter override (e.g., confidence threshold)


class SourceDomain(str, Enum):
    """Source domain that proposed the candidate."""

    AALMANAC = "AALMANAC"  # Term velocity / frequency analysis
    MW = "MW"  # Meaning Weave / semantic drift
    INTEGRITY = "INTEGRITY"  # SSI / trust surface
    BACKTEST = "BACKTEST"  # Failure analysis


class CandidateTarget(BaseModel):
    """Explicit target binding for candidate evaluation."""

    portfolios: List[str] = Field(default_factory=list)
    horizons: List[str] = Field(default_factory=list)
    score_metrics: List[str] = Field(default_factory=list)
    improvement_thresholds: Dict[str, float] = Field(default_factory=dict)
    no_regress_portfolios: List[str] = Field(default_factory=list)
    mechanism: str = ""


class MetricCandidate(BaseModel):
    """A proposed metric or parameter change."""

    candidate_id: str
    kind: CandidateKind
    source_domain: SourceDomain
    proposed_at: str  # ISO timestamp
    proposed_by: str  # Component that proposed it (e.g., "aalmanac_term_velocity")

    # What is being proposed
    name: str  # Metric name or param path
    description: str
    rationale: str  # Why this might help

    # For PARAM_TWEAK: what to change
    param_path: Optional[str] = None  # e.g., "forecast.confidence_threshold.H72H"
    current_value: Optional[Any] = None
    proposed_value: Optional[Any] = None

    # For METRIC/OPERATOR: implementation details
    implementation_spec: Optional[Dict[str, Any]] = None  # Ticket details

    # Sandbox expectations
    expected_improvement: Dict[str, Any] = Field(default_factory=dict)  # e.g., {"brier_delta": -0.05}
    target_horizons: List[str] = Field(default_factory=list)  # e.g., ["H72H", "H30D"]
    protected_horizons: List[str] = Field(default_factory=list)  # Cannot worsen these
    target: CandidateTarget = Field(default_factory=CandidateTarget)

    # Metadata
    vector_map_node_ref: Optional[str] = None  # If linked to vector map node
    priority: int = 5  # 1 (low) to 10 (high)
    enabled: bool = True

    # Provenance
    source_data_hash: Optional[str] = None  # Hash of delta that triggered proposal


class SandboxResult(BaseModel):
    """Result of sandbox testing a candidate."""

    sandbox_id: str
    candidate_id: str
    run_at: str  # ISO timestamp
    run_id: str  # e.g., "sandbox_run_20251226_001"

    # Test configuration
    hindcast_window_days: int  # How far back we tested
    cases_tested: int

    # Scores before/after
    score_before: Dict[str, float]  # e.g., {"brier_avg": 0.25, "log_avg": 0.52}
    score_after: Dict[str, float]  # e.g., {"brier_avg": 0.20, "log_avg": 0.45}
    score_delta: Dict[str, float]  # e.g., {"brier_delta": -0.05, "log_delta": -0.07}

    # Per-horizon breakdown
    horizon_scores: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    # e.g., {"H72H": {"before": {...}, "after": {...}, "delta": {...}}}

    # Pass/fail
    passed: bool
    pass_criteria: Dict[str, bool] = Field(default_factory=dict)
    # e.g., {"improvement_threshold": True, "no_regressions": True, "cost_bounds": True}

    failure_reasons: List[str] = Field(default_factory=list)

    # Portfolio-level reporting
    pass_gate: Optional[bool] = None
    portfolio_results: Dict[str, Any] = Field(default_factory=dict)
    portfolios_tested: List[str] = Field(default_factory=list)
    portfolio_score_delta_hash: Optional[str] = None

    # Provenance
    prev_hash: Optional[str] = None
    step_hash: Optional[str] = None


class StabilizationWindow(BaseModel):
    """Tracks consecutive sandbox runs for stabilization."""

    candidate_id: str
    window_size: int = 3  # Number of consecutive passes required
    consecutive_passes: int = 0
    consecutive_failures: int = 0
    last_run_at: Optional[str] = None  # ISO timestamp
    last_run_passed: Optional[bool] = None

    # History
    run_history: List[Dict[str, Any]] = Field(default_factory=list)
    # e.g., [{"run_id": "...", "passed": True, "run_at": "..."}, ...]

    def is_stable(self) -> bool:
        """Check if candidate has stabilized (N consecutive passes)."""
        return self.consecutive_passes >= self.window_size

    def record_run(self, sandbox_result: SandboxResult) -> None:
        """Record a sandbox run and update counters."""
        self.last_run_at = sandbox_result.run_at
        self.last_run_passed = sandbox_result.passed

        # Add to history
        self.run_history.append({
            "sandbox_id": sandbox_result.sandbox_id,
            "run_id": sandbox_result.run_id,
            "passed": sandbox_result.passed,
            "run_at": sandbox_result.run_at
        })

        # Update counters
        if sandbox_result.passed:
            self.consecutive_passes += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_passes = 0  # Reset on failure


class PromotionEntry(BaseModel):
    """Record of a promoted candidate."""

    promotion_id: str
    candidate_id: str
    promoted_at: str  # ISO timestamp
    promoted_by: str  # e.g., "promotion_gate_v0_1"

    # What was promoted
    kind: CandidateKind
    name: str
    description: str

    # Promotion action taken
    action_type: str  # "param_override", "implementation_ticket"
    action_details: Dict[str, Any] = Field(default_factory=dict)
    # For param_override: {"override_file": "...", "param_path": "...", "value": ...}
    # For implementation_ticket: {"ticket_file": "...", "implementation_spec": {...}}

    # Stabilization proof
    stabilization_window: Dict[str, Any] = Field(default_factory=dict)
    # e.g., {"window_size": 3, "consecutive_passes": 3, "run_ids": ["...", "...", "..."]}

    sandbox_results_summary: Dict[str, Any] = Field(default_factory=dict)
    # e.g., {"best_brier_delta": -0.08, "avg_improvement": 0.12, "runs_tested": 3}

    # Provenance
    prev_hash: Optional[str] = None
    step_hash: Optional[str] = None


class ImplementationTicket(BaseModel):
    """Implementation ticket for metric/operator candidates."""

    ticket_id: str
    candidate_id: str
    created_at: str  # ISO timestamp
    status: str = "pending"  # pending, in_progress, implemented, rejected

    # Ticket details
    kind: CandidateKind  # METRIC or OPERATOR
    name: str
    description: str
    rationale: str

    # Implementation spec
    implementation_spec: Dict[str, Any] = Field(default_factory=dict)
    # For metrics: {"formula": "...", "inputs": [...], "output_range": [...]}
    # For operators: {"signature": "...", "semantics": "...", "examples": [...]}

    # Sandbox proof
    sandbox_proof: List[str] = Field(default_factory=list)  # List of sandbox_ids
    stabilization_proof: Dict[str, Any] = Field(default_factory=dict)

    # Assignment
    assigned_to: Optional[str] = None
    implemented_at: Optional[str] = None
    implementation_notes: Optional[str] = None

    # Provenance
    ticket_file_path: Optional[str] = None


class CandidateFilter(BaseModel):
    """Filter criteria for querying candidates."""

    kind: Optional[CandidateKind] = None
    source_domain: Optional[SourceDomain] = None
    enabled_only: bool = True
    min_priority: Optional[int] = None
    max_priority: Optional[int] = None
    proposed_after: Optional[str] = None  # ISO timestamp
    proposed_before: Optional[str] = None
    target_horizon: Optional[str] = None  # e.g., "H72H"


class SandboxConfig(BaseModel):
    """Configuration for sandbox testing."""

    hindcast_window_days: int = 90  # How far back to test
    min_cases_required: int = 5  # Minimum cases for valid test
    improvement_threshold: float = 0.10  # Require 10% improvement
    regression_tolerance: float = 0.02  # Allow 2% regression on protected horizons
    cost_multiplier_max: float = 2.0  # Max 2x cost increase

    # Score weights
    brier_weight: float = 0.5
    log_weight: float = 0.3
    calibration_weight: float = 0.2


class PromotionCriteria(BaseModel):
    """Criteria for promoting a candidate."""

    require_stabilization: bool = True
    stabilization_window_size: int = 3  # Consecutive passes required
    min_improvement_pct: float = 10.0  # Minimum 10% improvement
    allow_regressions: bool = False  # No regressions on protected horizons
    max_cost_increase_pct: float = 50.0  # Max 50% cost increase

    # Auto-promotion settings
    auto_promote_param_tweaks: bool = True  # Auto-apply param tweaks
    auto_promote_metrics: bool = False  # Metrics require manual review
    auto_promote_operators: bool = False  # Operators require manual review


# Helper functions

def generate_candidate_id(kind: CandidateKind, source_domain: SourceDomain, timestamp: str) -> str:
    """
    Generate deterministic candidate ID.

    Format: cand_{kind}_{domain}_{timestamp_hash}
    Example: cand_param_tweak_AALMANAC_20251226_abc123
    """
    from abraxas.core.provenance import hash_canonical_json
    import json

    data = {
        "kind": kind.value,
        "source_domain": source_domain.value,
        "timestamp": timestamp
    }
    short_hash = hash_canonical_json(data)[:8]
    return f"cand_{kind.value}_{source_domain.value}_{timestamp[:10]}_{short_hash}"


def generate_sandbox_id(candidate_id: str, run_at: str) -> str:
    """
    Generate deterministic sandbox ID.

    Format: sbx_{candidate_id}_{timestamp_hash}
    Example: sbx_cand_param_tweak_AALMANAC_20251226_abc123_20251226_def456
    """
    from abraxas.core.provenance import hash_canonical_json
    import json

    data = {
        "candidate_id": candidate_id,
        "run_at": run_at
    }
    short_hash = hash_canonical_json(data)[:8]
    return f"sbx_{candidate_id}_{run_at[:10]}_{short_hash}"


def generate_promotion_id(candidate_id: str, promoted_at: str) -> str:
    """
    Generate deterministic promotion ID.

    Format: promo_{candidate_id}_{timestamp_hash}
    Example: promo_cand_param_tweak_AALMANAC_20251226_abc123_20251226_ghi789
    """
    from abraxas.core.provenance import hash_canonical_json
    import json

    data = {
        "candidate_id": candidate_id,
        "promoted_at": promoted_at
    }
    short_hash = hash_canonical_json(data)[:8]
    return f"promo_{candidate_id}_{promoted_at[:10]}_{short_hash}"


def generate_ticket_id(candidate_id: str, created_at: str) -> str:
    """
    Generate deterministic ticket ID.

    Format: ticket_{kind}_{timestamp_hash}
    Example: ticket_metric_20251226_jkl012
    """
    from abraxas.core.provenance import hash_canonical_json
    import json

    data = {
        "candidate_id": candidate_id,
        "created_at": created_at
    }
    short_hash = hash_canonical_json(data)[:8]
    return f"ticket_{created_at[:10]}_{short_hash}"
