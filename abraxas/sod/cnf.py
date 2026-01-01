"""CNF (Counter-Narrative Forecaster): Generates counter-narrative strategies.

Input: Cascade scenarios from NCP
Output: Counter-narrative strategies with effectiveness scores

Each strategy includes:
- Intervention points
- Effectiveness score [0,1]
- Resource requirements
"""

from __future__ import annotations

from typing import List
from uuid import uuid4

from abraxas.sod.models import ScenarioEnvelope, CounterNarrativeStrategy


class CounterNarrativeForecaster:
    """
    Counter-Narrative Forecaster (CNF).

    Generates counter-narrative strategies for cascade scenarios.
    v1.4: Deterministic heuristics only, no LLM integration.
    """

    def __init__(self, *, effectiveness_threshold: float = 0.3):
        """
        Initialize CNF.

        Args:
            effectiveness_threshold: Minimum effectiveness score for inclusion
        """
        self.effectiveness_threshold = effectiveness_threshold

    def forecast(
        self, scenario_envelope: ScenarioEnvelope
    ) -> List[CounterNarrativeStrategy]:
        """
        Generate counter-narrative strategies for a scenario envelope.

        Args:
            scenario_envelope: Scenario envelope from NCP

        Returns:
            List of CounterNarrativeStrategy objects
        """
        strategies = []

        for path in scenario_envelope.paths:
            # Generate strategies based on path characteristics
            path_strategies = self._generate_strategies_for_path(path)
            strategies.extend(path_strategies)

        # Deduplicate and sort by effectiveness
        unique_strategies = self._deduplicate_strategies(strategies)
        filtered = [
            s for s in unique_strategies if s.effectiveness_score >= self.effectiveness_threshold
        ]
        return sorted(filtered, key=lambda s: s.effectiveness_score, reverse=True)

    def _generate_strategies_for_path(
        self, path
    ) -> List[CounterNarrativeStrategy]:
        """Generate strategies for a single path."""
        strategies = []

        # Strategy 1: Early intervention (for high-probability paths)
        if path.probability > 0.5:
            effectiveness = path.probability * 0.7  # Early intervention more effective
            strategies.append(
                CounterNarrativeStrategy(
                    strategy_id=f"early-{uuid4().hex[:8]}",
                    description="Early intervention to disrupt cascade initiation",
                    intervention_points=[
                        "At trigger detection",
                        "During first intermediate state",
                    ],
                    effectiveness_score=effectiveness,
                    resource_requirements="Moderate: Monitoring + rapid response team",
                )
            )

        # Strategy 2: Credibility injection (for coordinated campaigns)
        if "Coordinated" in path.trigger or "Artificial" in path.terminus:
            effectiveness = 0.6
            strategies.append(
                CounterNarrativeStrategy(
                    strategy_id=f"credibility-{uuid4().hex[:8]}",
                    description="Inject high-credibility counter-narrative",
                    intervention_points=[
                        "During amplification phase",
                        "Before saturation",
                    ],
                    effectiveness_score=effectiveness,
                    resource_requirements="High: Trusted sources + platform partnerships",
                )
            )

        # Strategy 3: Inoculation (for viral spread)
        if "viral" in path.path_id or path.duration_hours < 72:
            effectiveness = 0.5
            strategies.append(
                CounterNarrativeStrategy(
                    strategy_id=f"inoculation-{uuid4().hex[:8]}",
                    description="Pre-emptive inoculation against misinformation",
                    intervention_points=["Before cascade begins"],
                    effectiveness_score=effectiveness,
                    resource_requirements="Low: Educational content distribution",
                )
            )

        # Strategy 4: Decay acceleration (for slow decay paths)
        if "decay" in path.path_id or "Dormant" in path.intermediates:
            effectiveness = 0.4
            strategies.append(
                CounterNarrativeStrategy(
                    strategy_id=f"decay-{uuid4().hex[:8]}",
                    description="Accelerate natural decay through disengagement",
                    intervention_points=[
                        "During saturation phase",
                        "Early dormant transition",
                    ],
                    effectiveness_score=effectiveness,
                    resource_requirements="Low: Passive monitoring",
                )
            )

        # Strategy 5: Revival prevention (for revival waves)
        if "revival" in path.path_id or "Revival" in path.trigger:
            effectiveness = 0.55
            strategies.append(
                CounterNarrativeStrategy(
                    strategy_id=f"prevention-{uuid4().hex[:8]}",
                    description="Prevent revival through context provision",
                    intervention_points=["At mutation detection", "During proto revival"],
                    effectiveness_score=effectiveness,
                    resource_requirements="Moderate: Context aggregation + distribution",
                )
            )

        return strategies

    def _deduplicate_strategies(
        self, strategies: List[CounterNarrativeStrategy]
    ) -> List[CounterNarrativeStrategy]:
        """Deduplicate strategies by description (simple heuristic)."""
        seen = set()
        unique = []
        for strategy in strategies:
            if strategy.description not in seen:
                seen.add(strategy.description)
                unique.append(strategy)
        return unique
