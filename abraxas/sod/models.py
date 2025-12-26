"""SOD Models: Shared data structures for Second-Order Dynamics modules.

Defines:
- SODInput: Input data for SOD modules
- ScenarioPath: Single cascade path with triggers and probabilities
- ScenarioEnvelope: Complete scenario output with paths and falsifiers
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from abraxas.core.provenance import Provenance
from abraxas.core.temporal_tau import TauSnapshot
from abraxas.integrity.composites import CompositeRiskIndices
from abraxas.weather.affinity import AffinityScore


@dataclass(frozen=True)
class SODInput:
    """Input data bundle for SOD modules."""

    tau_snapshot: TauSnapshot
    risk_indices: Optional[CompositeRiskIndices]
    affinity_score: Optional[AffinityScore]
    context: Dict[str, Any]  # Additional context data


@dataclass(frozen=True)
class ScenarioPath:
    """Single cascade path with triggers, probability, and intermediates."""

    path_id: str
    trigger: str  # Description of initiating event
    probability: float  # [0,1] deterministic heuristic score
    duration_hours: int  # Estimated duration
    intermediates: List[str]  # Intermediate states
    terminus: str  # Final state


@dataclass(frozen=True)
class ScenarioEnvelope:
    """Complete scenario output with paths, falsifiers, and provenance."""

    scenario_id: str
    paths: List[ScenarioPath]
    falsifiers: List[str]  # Counterfactual conditions that would invalidate scenario
    confidence: str  # LOW/MED/HIGH
    provenance: Provenance


@dataclass(frozen=True)
class CounterNarrativeStrategy:
    """Counter-narrative strategy with intervention points."""

    strategy_id: str
    description: str
    intervention_points: List[str]  # Points where intervention is effective
    effectiveness_score: float  # [0,1] estimated effectiveness
    resource_requirements: str  # Description of resources needed


@dataclass(frozen=True)
class FatigueThreshold:
    """Epistemic fatigue threshold assessment."""

    threshold: float  # [0,1] current fatigue level
    saturation_risk: str  # LOW/MED/HIGH
    exposure_density: float  # Exposures per time unit
    declining_engagement: bool  # Engagement declining flag


@dataclass(frozen=True)
class SusceptibilityProfile:
    """Susceptibility profile for weather types."""

    profile_id: str
    weather_affinities: Dict[str, float]  # WeatherType -> susceptibility [0,1]
    demographic_factors: Dict[str, Any]
    historical_resonance: float  # [0,1] historical affinity


@dataclass(frozen=True)
class RecoveryTimeline:
    """Recovery and re-stabilization timeline."""

    timeline_id: str
    stabilization_probability: float  # [0,1]
    recovery_duration_hours: int
    intervention_impact: float  # [0,1] impact of interventions
    baseline_return_date: Optional[str]  # ISO8601Z
