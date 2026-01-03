"""Budget dimension schemas for Universal Budget Vector.

Universal Tuning Plane v0.4 - Budget tracking schemas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetDimension:
    """Single budget dimension with measured value, budget, and hard limit.

    Attributes:
        measured: Actual measured value
        budget: Soft budget (warning threshold)
        hard_limit: Hard limit (blocks promotion if exceeded)
    """

    measured: float
    budget: float | None = None
    hard_limit: float | None = None

    def is_within_budget(self) -> bool:
        """Check if measured value is within budget."""
        if self.hard_limit is not None and self.measured > self.hard_limit:
            return False
        if self.budget is not None and self.measured > self.budget:
            return False
        return True

    def utilization_ratio(self) -> float:
        """Compute utilization ratio (measured / budget).

        Returns:
            Utilization ratio (1.0 = at budget, >1.0 = over budget)
        """
        if self.budget is None or self.budget == 0:
            return 0.0
        return self.measured / self.budget
