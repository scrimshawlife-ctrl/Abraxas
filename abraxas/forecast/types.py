"""
Forecast Object Model

Defines core types for FBE (Forecast Branch Ensemble):
- Horizon: Time windows for forecasts
- Branch: Single scenario with probability mass
- EnsembleState: Collection of branches for a topic/horizon
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Horizon(str, Enum):
    """Forecast time horizons."""

    H72H = "H72H"  # 72 hours
    H30D = "H30D"  # 30 days
    H90D = "H90D"  # 90 days
    H1Y = "H1Y"  # 1 year
    H2Y = "H2Y"  # 2 years
    H5Y = "H5Y"  # 5 years

    def to_hours(self) -> int:
        """Convert horizon to hours."""
        mapping = {
            "H72H": 72,
            "H30D": 720,
            "H90D": 2160,
            "H1Y": 8760,
            "H2Y": 17520,
            "H5Y": 43800,
        }
        return mapping[self.value]


class Branch(BaseModel):
    """
    Single forecast branch (scenario).

    Represents one possible future state with probability mass.
    """

    branch_id: str = Field(description="Deterministic hash-based ID")
    horizon: Horizon = Field(description="Forecast time horizon")
    segment: str = Field(
        description="Segment: core, peripheral", pattern="^(core|peripheral)$"
    )
    narrative: str = Field(
        description="Narrative: N1_primary, N2_counter",
        pattern="^(N1_primary|N2_counter)$",
    )

    label: str = Field(
        description="Branch label (conservative, base, shock, etc.)"
    )
    description: str = Field(description="Human-readable scenario description")

    # Probability mass
    p: float = Field(description="Probability mass [0..1]", ge=0, le=1)
    p_min: float = Field(
        default=0.0, description="Confidence band lower bound", ge=0, le=1
    )
    p_max: float = Field(
        default=1.0, description="Confidence band upper bound", ge=0, le=1
    )

    # Temporal resolution
    tau_window_hours: int = Field(
        description="τ evaluation window in hours", gt=0
    )

    # Outcome specification (compatible with backtest TriggerSpec)
    triggers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Conditions that would confirm this branch",
    )
    falsifiers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Conditions that would invalidate this branch",
    )

    # Integrity awareness
    manipulation_exposure: Dict[str, float] = Field(
        default_factory=dict,
        description="Sensitivity to manipulation (e.g., SSI_sensitivity: 0.7)",
    )

    # Provenance
    provenance: Dict[str, Any] = Field(
        default_factory=dict, description="Creation/update metadata"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When branch was created",
    )
    last_updated_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When branch probability was last updated",
    )


class EnsembleState(BaseModel):
    """
    Forecast ensemble for a single topic/horizon/segment/narrative.

    Contains multiple branches with probability mass summing to 1.0.
    """

    ensemble_id: str = Field(
        description="Deterministic hash of (topic_key+horizon+segment+narrative)"
    )

    topic_key: str = Field(
        description="Topic identifier (e.g., 'deepfake_pollution', 'mw_cluster:<id>')"
    )
    horizon: Horizon = Field(description="Forecast horizon")
    segment: str = Field(description="Segment: core, peripheral")
    narrative: str = Field(description="Narrative: N1_primary, N2_counter")

    branches: List[Branch] = Field(
        description="Branch scenarios with probability mass"
    )

    # Metadata
    last_updated_ts: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When ensemble was last updated",
    )
    provenance: Dict[str, Any] = Field(
        default_factory=dict, description="Creation/update provenance"
    )

    def validate_probabilities(self) -> bool:
        """Validate that branch probabilities sum to ~1.0."""
        total = sum(b.p for b in self.branches)
        return abs(total - 1.0) < 0.01  # Allow small floating point error

    def get_branch(self, branch_id: str) -> Optional[Branch]:
        """Get branch by ID."""
        for branch in self.branches:
            if branch.branch_id == branch_id:
                return branch
        return None
