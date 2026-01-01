"""
Scoreboard Types

Data structures for forecast outcomes and scoring results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ForecastOutcome(BaseModel):
    """
    Observed outcome for a forecast branch.

    Links to backtest case that evaluated the branch.
    """

    case_id: str = Field(description="Backtest case ID")
    ensemble_id: str = Field(description="Ensemble ID")
    branch_id: str = Field(description="Branch ID")

    observed: bool = Field(description="Whether branch outcome occurred")
    observed_ts: datetime = Field(description="When outcome was observed")

    provenance: Dict[str, Any] = Field(
        default_factory=dict, description="Backtest provenance"
    )


class CalibrationBin(BaseModel):
    """
    Calibration bin for a probability range.

    Tracks predicted vs observed frequency.
    """

    bin_label: str = Field(description="Bin label (e.g., '60-70%')")
    predicted_p_avg: float = Field(description="Average predicted probability in bin")
    observed_frequency: float = Field(description="Actual outcome frequency")
    n: int = Field(description="Number of forecasts in bin")


class ScoreResult(BaseModel):
    """
    Aggregate scoring result for a horizon/segment/narrative.
    """

    score_id: str = Field(description="Unique score result ID")
    ts: datetime = Field(
        default_factory=lambda: datetime.now(), description="When score was computed"
    )

    horizon: str = Field(description="Forecast horizon (H72H, H30D, etc.)")
    segment: str = Field(default="", description="Segment (core, peripheral)")
    narrative: str = Field(default="", description="Narrative (N1_primary, N2_counter)")

    # Accuracy metrics
    brier_avg: Optional[float] = Field(default=None, description="Average Brier score")
    log_avg: Optional[float] = Field(default=None, description="Average log score")

    # Calibration
    calibration_bins: List[CalibrationBin] = Field(
        default_factory=list, description="Calibration bin results"
    )

    # Coverage
    coverage: Dict[str, int] = Field(
        default_factory=dict,
        description="Outcome coverage (hit, miss, abstain counts)",
    )

    abstain_rate: float = Field(default=0.0, description="Abstain rate")

    # Metadata
    cases_scored: int = Field(default=0, description="Number of cases scored")
    notes: List[str] = Field(default_factory=list, description="Notes")

    provenance: Dict[str, Any] = Field(
        default_factory=dict, description="Scoring provenance"
    )
