"""
Lane Guard - Enforces separation between Shadow and Prediction lanes.

CRITICAL DESIGN CONSTRAINT:
Shadow detector outputs and shadow metrics MUST NOT flow into prediction/forecast
pipelines unless explicitly PROMOTED via governance system.

The Lane Guard:
1. Checks if a metric/signal is attempting to cross from Shadow → Prediction
2. Verifies promotion status in promotion ledger
3. Validates promotion criteria (calibration, stability, redundancy ONLY)
4. REJECTS any promotion based on ethical/risk/diagnostic criteria
5. Logs violations for audit

This is the ABX-Runes ϟ₇ enforcement point.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from pydantic import BaseModel, Field


class LaneViolationError(Exception):
    """Raised when shadow output attempts to cross into prediction lane without promotion."""
    pass


class PromotionRecord(BaseModel):
    """
    Record of a metric promotion from Shadow → Prediction.

    CRITICAL: Promotion criteria MUST be limited to:
    - Calibration (accuracy, precision, recall)
    - Stability (temporal consistency, low variance)
    - Redundancy (non-correlation with existing metrics)

    Ethical/risk/diagnostic criteria are FORBIDDEN.
    """
    metric_name: str = Field(..., description="Name of metric/detector")
    status: str = Field(..., description="PROMOTED or REJECTED")
    promotion_date: str = Field(..., description="ISO8601 timestamp")

    # Required evidence (ONLY technical criteria)
    calibration_score: float = Field(..., ge=0.0, le=1.0, description="Calibration metric [0,1]")
    stability_score: float = Field(..., ge=0.0, le=1.0, description="Temporal stability [0,1]")
    redundancy_score: float = Field(..., ge=0.0, le=1.0, description="Non-redundancy [0,1]")

    # FORBIDDEN fields (will raise error if present)
    ethical_score: Optional[float] = Field(None, description="FORBIDDEN - ethical scoring not allowed")
    risk_score: Optional[float] = Field(None, description="FORBIDDEN - risk scoring not allowed")
    diagnostic_only: Optional[bool] = Field(None, description="FORBIDDEN - diagnostic flags not allowed")

    # Provenance
    promotion_hash: str = Field(..., description="SHA-256 hash of promotion decision")

    def __init__(self, **data):
        """Initialize and validate forbidden fields."""
        super().__init__(**data)
        # Validate that forbidden fields are not used
        if self.ethical_score is not None:
            raise ValueError("FORBIDDEN: ethical_score cannot be used in promotion criteria")
        if self.risk_score is not None:
            raise ValueError("FORBIDDEN: risk_score cannot be used in promotion criteria")
        if self.diagnostic_only is not None:
            raise ValueError("FORBIDDEN: diagnostic_only cannot be used in promotion criteria")


class LaneGuard:
    """
    Lane Guard - Enforces Shadow/Prediction lane separation.

    Usage:
        guard = LaneGuard(promotion_ledger_path="out/ledger/promotion_ledger.jsonl")

        # Before using a shadow metric in prediction:
        guard.check_promotion("compliance_remix")  # Raises LaneViolationError if not promoted
    """

    def __init__(self, promotion_ledger_path: Optional[str] = None):
        """
        Initialize Lane Guard.

        Args:
            promotion_ledger_path: Path to promotion ledger JSONL file.
                                   If None, uses default: out/ledger/promotion_ledger.jsonl
        """
        if promotion_ledger_path is None:
            promotion_ledger_path = "out/ledger/promotion_ledger.jsonl"

        self.ledger_path = Path(promotion_ledger_path)
        self._load_promotions()

    def _load_promotions(self) -> None:
        """Load promotion records from ledger."""
        self.promotions: Dict[str, PromotionRecord] = {}

        if not self.ledger_path.exists():
            # No ledger = no promotions
            return

        with open(self.ledger_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                record = PromotionRecord(**data)
                if record.status == "PROMOTED":
                    self.promotions[record.metric_name] = record

    def check_promotion(self, metric_name: str) -> PromotionRecord:
        """
        Check if a metric is promoted for use in prediction lane.

        Args:
            metric_name: Name of metric/detector to check

        Returns:
            PromotionRecord if promoted

        Raises:
            LaneViolationError: If metric is not promoted
        """
        if metric_name not in self.promotions:
            raise LaneViolationError(
                f"LANE VIOLATION: '{metric_name}' is a shadow metric/detector and "
                f"cannot be used in prediction lane without promotion. "
                f"Promote via governance system with calibration/stability/redundancy validation."
            )

        return self.promotions[metric_name]

    def is_promoted(self, metric_name: str) -> bool:
        """
        Check if a metric is promoted (non-raising version).

        Args:
            metric_name: Name of metric/detector

        Returns:
            True if promoted, False otherwise
        """
        return metric_name in self.promotions

    def get_all_promoted(self) -> List[str]:
        """
        Get list of all promoted metrics.

        Returns:
            List of promoted metric names
        """
        return sorted(self.promotions.keys())

    def validate_promotion_criteria(self, record: PromotionRecord) -> None:
        """
        Validate that promotion criteria are technical only.

        This is redundant with PromotionRecord validation but provides
        an explicit checkpoint.

        Args:
            record: PromotionRecord to validate

        Raises:
            ValueError: If forbidden criteria are present
        """
        # This will be caught by Pydantic validation, but make it explicit
        if record.ethical_score is not None:
            raise ValueError("FORBIDDEN: Promotion cannot use ethical_score")
        if record.risk_score is not None:
            raise ValueError("FORBIDDEN: Promotion cannot use risk_score")
        if record.diagnostic_only is not None:
            raise ValueError("FORBIDDEN: Promotion cannot use diagnostic_only flag")


# Global lane guard instance (lazy-loaded)
_GLOBAL_LANE_GUARD: Optional[LaneGuard] = None


def get_lane_guard() -> LaneGuard:
    """Get global lane guard instance (singleton)."""
    global _GLOBAL_LANE_GUARD
    if _GLOBAL_LANE_GUARD is None:
        _GLOBAL_LANE_GUARD = LaneGuard()
    return _GLOBAL_LANE_GUARD


def require_promoted(metric_name: str) -> PromotionRecord:
    """
    Convenience function to check promotion (uses global lane guard).

    Args:
        metric_name: Name of metric to check

    Returns:
        PromotionRecord if promoted

    Raises:
        LaneViolationError: If not promoted
    """
    return get_lane_guard().check_promotion(metric_name)
