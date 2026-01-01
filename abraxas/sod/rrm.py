"""RRM (Recovery & Re-Stabilization Model): Models return to baseline after disruption.

Input: Post-cascade state, intervention history
Output: Recovery timeline, stabilization probability

Models recovery trajectories after cascade events.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import uuid4

from abraxas.sod.models import RecoveryTimeline, CounterNarrativeStrategy


class RecoveryReStabilizationModel:
    """
    Recovery & Re-Stabilization Model (RRM).

    Models return to baseline after narrative cascade disruption.
    v1.4: Deterministic heuristics based on intervention impact and cascade severity.
    """

    def __init__(
        self,
        *,
        baseline_recovery_hours: int = 336,  # 2 weeks default
        intervention_boost: float = 0.3,
    ):
        """
        Initialize RRM.

        Args:
            baseline_recovery_hours: Default recovery duration without intervention
            intervention_boost: Boost to stabilization probability from interventions
        """
        self.baseline_recovery_hours = baseline_recovery_hours
        self.intervention_boost = intervention_boost

    def model_recovery(
        self,
        cascade_severity: float,  # [0,1] how severe was the cascade
        interventions: List[CounterNarrativeStrategy],
        current_time_utc: Optional[str] = None,
    ) -> RecoveryTimeline:
        """
        Model recovery timeline from cascade event.

        Args:
            cascade_severity: Severity of cascade [0,1]
            interventions: Counter-narrative interventions applied
            current_time_utc: Current time (ISO8601Z)

        Returns:
            RecoveryTimeline with stabilization probability
        """
        # Base recovery duration scales with severity
        base_duration = int(self.baseline_recovery_hours * (1.0 + cascade_severity))

        # Intervention impact (average effectiveness)
        if interventions:
            avg_effectiveness = sum(
                s.effectiveness_score for s in interventions
            ) / len(interventions)
            intervention_impact = avg_effectiveness
        else:
            intervention_impact = 0.0

        # Adjusted recovery duration (interventions reduce duration)
        recovery_duration_hours = int(
            base_duration * (1.0 - intervention_impact * 0.3)
        )

        # Stabilization probability
        # Higher with interventions, lower with higher severity
        base_prob = 0.5
        prob_boost = intervention_impact * self.intervention_boost
        prob_penalty = cascade_severity * 0.2
        stabilization_probability = min(
            base_prob + prob_boost - prob_penalty, 1.0
        )

        # Baseline return date (if current time provided)
        baseline_return_date = None
        if current_time_utc:
            from datetime import datetime, timezone, timedelta

            current_dt = datetime.fromisoformat(
                current_time_utc.replace("Z", "+00:00")
            )
            return_dt = current_dt + timedelta(hours=recovery_duration_hours)
            baseline_return_date = return_dt.isoformat().replace("+00:00", "Z")

        timeline_id = str(uuid4())
        return RecoveryTimeline(
            timeline_id=timeline_id,
            stabilization_probability=stabilization_probability,
            recovery_duration_hours=recovery_duration_hours,
            intervention_impact=intervention_impact,
            baseline_return_date=baseline_return_date,
        )
