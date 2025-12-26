"""SPM (Susceptibility Profile Mapper): Maps susceptibility profiles per weather type.

Input: Demographic/context features, historical affinity
Output: Susceptibility profile per weather type [0,1]

Deterministic mapping: features → susceptibility.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import uuid4

from abraxas.sod.models import SusceptibilityProfile
from abraxas.weather.registry import WeatherType


class SusceptibilityProfileMapper:
    """
    Susceptibility Profile Mapper (SPM).

    Maps demographic/context features to susceptibility per weather type.
    v1.4: Deterministic heuristics only, no ML models.
    """

    def __init__(self):
        """Initialize SPM."""
        pass

    def map_profile(
        self,
        demographic_factors: Dict[str, Any],
        historical_affinities: Dict[str, float],
    ) -> SusceptibilityProfile:
        """
        Map susceptibility profile from features.

        Args:
            demographic_factors: Demographic/context features (e.g., age, region, context)
            historical_affinities: Historical affinity scores per weather type

        Returns:
            SusceptibilityProfile with weather affinities
        """
        weather_affinities = {}

        # Compute susceptibility for each weather type
        for weather_type in WeatherType:
            susceptibility = self._compute_susceptibility(
                weather_type, demographic_factors, historical_affinities
            )
            weather_affinities[weather_type.value] = susceptibility

        # Compute historical resonance (average historical affinity)
        historical_resonance = (
            sum(historical_affinities.values()) / len(historical_affinities)
            if historical_affinities
            else 0.0
        )

        profile_id = str(uuid4())
        return SusceptibilityProfile(
            profile_id=profile_id,
            weather_affinities=weather_affinities,
            demographic_factors=demographic_factors,
            historical_resonance=historical_resonance,
        )

    def _compute_susceptibility(
        self,
        weather_type: WeatherType,
        demographic_factors: Dict[str, Any],
        historical_affinities: Dict[str, float],
    ) -> float:
        """Compute susceptibility for a single weather type."""
        # Base susceptibility from historical affinity
        base = historical_affinities.get(weather_type.value, 0.5)

        # Adjust based on demographic factors (simple heuristics)
        # Example: younger demographics more susceptible to emergence storms
        if weather_type == WeatherType.MW_03_EMERGENCE_STORM:
            age = demographic_factors.get("age", 30)
            if age < 25:
                base *= 1.2
        elif weather_type == WeatherType.MW_02_COMPRESSION_STABILITY:
            age = demographic_factors.get("age", 30)
            if age > 40:
                base *= 1.1

        # Clamp to [0,1]
        return min(base, 1.0)
