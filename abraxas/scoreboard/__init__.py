"""
Scoreboard v0.1

Accuracy measurement for probabilistic forecasts:
- Brier score: (p - y)²
- Log score: -log(p)
- Calibration: Do 70% predictions happen 70% of the time?

All scoring deterministic, fully traceable via ledgers.
"""

from abraxas.scoreboard.types import (
    ForecastOutcome,
    ScoreResult,
)
from abraxas.scoreboard.scoring import (
    brier_score,
    log_score,
    update_calibration_bins,
)
from abraxas.scoreboard.aggregate import aggregate_scores_for_cases
from abraxas.scoreboard.ledger import (
    ScoreLedger,
)
from abraxas.scoreboard.components import aggregate_component_outcomes
from abraxas.scoreboard.component_ledger import ComponentScoreLedger, write_component_score_summary

__all__ = [
    # Types
    "ForecastOutcome",
    "ScoreResult",
    # Scoring functions
    "brier_score",
    "log_score",
    "update_calibration_bins",
    "aggregate_scores_for_cases",
    # Ledger
    "ScoreLedger",
    "aggregate_component_outcomes",
    "ComponentScoreLedger",
    "write_component_score_summary",
]
