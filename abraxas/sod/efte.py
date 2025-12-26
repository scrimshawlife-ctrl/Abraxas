"""EFTE (Epistemic Fatigue Threshold Engine): Models declining engagement under saturation.

Input: Exposure history, RRS scores, temporal density
Output: Fatigue threshold [0,1], saturation risk

Models epistemic fatigue from repetition saturation.
"""

from __future__ import annotations

from typing import List

from abraxas.sod.models import FatigueThreshold


class EpistemicFatigueThresholdEngine:
    """
    Epistemic Fatigue Threshold Engine (EFTE).

    Models declining engagement under repetition saturation.
    v1.4: Deterministic heuristics based on exposure density and RRS.
    """

    def __init__(
        self,
        *,
        saturation_threshold: float = 0.7,
        decline_window_hours: int = 168,
    ):
        """
        Initialize EFTE.

        Args:
            saturation_threshold: Threshold for HIGH saturation risk
            decline_window_hours: Window for measuring engagement decline
        """
        self.saturation_threshold = saturation_threshold
        self.decline_window_hours = decline_window_hours

    def compute_fatigue(
        self,
        exposure_count: int,
        time_window_hours: int,
        rrs_score: float,
        engagement_trend: List[float],
    ) -> FatigueThreshold:
        """
        Compute epistemic fatigue threshold.

        Args:
            exposure_count: Number of exposures to content/narrative
            time_window_hours: Time window for exposure count
            rrs_score: Repetition/Redundancy Score [0,1]
            engagement_trend: Time-series of engagement scores [0,1]

        Returns:
            FatigueThreshold with saturation risk assessment
        """
        # Exposure density (exposures per hour)
        if time_window_hours > 0:
            exposure_density = exposure_count / time_window_hours
        else:
            exposure_density = 0.0

        # Fatigue increases with exposure density and RRS
        # Heuristic: density * RRS, clamped to [0,1]
        base_fatigue = min(exposure_density * rrs_score, 1.0)

        # Adjust for engagement decline
        declining_engagement = self._is_declining(engagement_trend)
        if declining_engagement:
            # Boost fatigue if engagement is declining
            fatigue_threshold = min(base_fatigue * 1.5, 1.0)
        else:
            fatigue_threshold = base_fatigue

        # Compute saturation risk
        if fatigue_threshold >= self.saturation_threshold:
            saturation_risk = "HIGH"
        elif fatigue_threshold >= 0.4:
            saturation_risk = "MED"
        else:
            saturation_risk = "LOW"

        return FatigueThreshold(
            threshold=fatigue_threshold,
            saturation_risk=saturation_risk,
            exposure_density=exposure_density,
            declining_engagement=declining_engagement,
        )

    def _is_declining(self, engagement_trend: List[float]) -> bool:
        """Check if engagement is declining."""
        if len(engagement_trend) < 2:
            return False

        # Simple heuristic: compare first half to second half
        mid = len(engagement_trend) // 2
        first_half_avg = sum(engagement_trend[:mid]) / mid
        second_half_avg = sum(engagement_trend[mid:]) / (len(engagement_trend) - mid)

        return second_half_avg < first_half_avg * 0.8  # 20% decline threshold
