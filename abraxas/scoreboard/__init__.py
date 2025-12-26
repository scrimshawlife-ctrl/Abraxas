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
from abraxas.scoreboard.ledger import (
    ScoreLedger,
)

__all__ = [
    # Types
    "ForecastOutcome",
    "ScoreResult",
    # Scoring functions
    "brier_score",
    "log_score",
    "update_calibration_bins",
    # Ledger
    "ScoreLedger",
]
