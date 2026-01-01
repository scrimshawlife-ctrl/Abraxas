"""Memetic Weather Registry: MW-01 through MW-05 canonical types.

Canonical weather types for symbolic environmental classification.
Each type has specific τ signature patterns and archetype affinities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class WeatherType(str, Enum):
    """Canonical memetic weather types."""

    MW_01_SYMBOLIC_DRIFT = "MW-01"  # High replacement pressure
    MW_02_COMPRESSION_STABILITY = "MW-02"  # Low volatility
    MW_03_EMERGENCE_STORM = "MW-03"  # Rapid new symbol introduction
    MW_04_SEMANTIC_SATURATION = "MW-04"  # Dormant transitions
    MW_05_REVIVAL_WAVE = "MW-05"  # Mutation-driven re-emergence


@dataclass(frozen=True)
class WeatherTypeDefinition:
    """Complete definition for a weather type."""

    code: str  # MW-01, MW-02, etc.
    name: str
    description: str
    tau_velocity_min: float  # Minimum τᵥ threshold
    tau_velocity_max: float  # Maximum τᵥ threshold
    tau_half_life_min: float  # Minimum τₕ threshold (hours)
    tau_half_life_max: float  # Maximum τₕ threshold (hours)
    archetype_affinities: List[str]  # Preferred SA classes
    tone_flags: List[str]  # Tone alignment flags


# Canonical registry of weather types
WEATHER_REGISTRY: Dict[WeatherType, WeatherTypeDefinition] = {
    WeatherType.MW_01_SYMBOLIC_DRIFT: WeatherTypeDefinition(
        code="MW-01",
        name="Symbolic Drift",
        description="High replacement pressure, rising transparency flux",
        tau_velocity_min=0.5,
        tau_velocity_max=999.0,
        tau_half_life_min=0.0,
        tau_half_life_max=999.0,
        archetype_affinities=["eggcorn", "compression", "substitution"],
        tone_flags=["humor", "intimacy"],
    ),
    WeatherType.MW_02_COMPRESSION_STABILITY: WeatherTypeDefinition(
        code="MW-02",
        name="Compression Stability",
        description="Low τᵥ, stable τₕ, established patterns",
        tau_velocity_min=-0.1,
        tau_velocity_max=0.1,
        tau_half_life_min=168.0,  # 7 days
        tau_half_life_max=999.0,
        archetype_affinities=["idiom", "established_slang", "canonical"],
        tone_flags=["authority", "neutral"],
    ),
    WeatherType.MW_03_EMERGENCE_STORM: WeatherTypeDefinition(
        code="MW-03",
        name="Emergence Storm",
        description="Rapid new symbol introduction, high τᵥ, volatile τₕ",
        tau_velocity_min=1.0,
        tau_velocity_max=999.0,
        tau_half_life_min=0.0,
        tau_half_life_max=48.0,  # 2 days
        archetype_affinities=["proto", "neologism", "viral"],
        tone_flags=["novelty", "excitement", "irony"],
    ),
    WeatherType.MW_04_SEMANTIC_SATURATION: WeatherTypeDefinition(
        code="MW-04",
        name="Semantic Saturation",
        description="Dormant transitions, declining engagement",
        tau_velocity_min=-999.0,
        tau_velocity_max=-0.1,
        tau_half_life_min=0.0,
        tau_half_life_max=168.0,  # 7 days
        archetype_affinities=["fading", "obsolete", "overused"],
        tone_flags=["fatigue", "nihilism"],
    ),
    WeatherType.MW_05_REVIVAL_WAVE: WeatherTypeDefinition(
        code="MW-05",
        name="Revival Wave",
        description="Mutation-driven re-emergence",
        tau_velocity_min=0.3,
        tau_velocity_max=999.0,
        tau_half_life_min=0.0,
        tau_half_life_max=999.0,
        archetype_affinities=["revival", "mutation", "nostalgia"],
        tone_flags=["irony", "nostalgia", "humor"],
    ),
}


def get_weather_definition(weather_type: WeatherType) -> WeatherTypeDefinition:
    """
    Get canonical definition for a weather type.

    Args:
        weather_type: Weather type enum value

    Returns:
        WeatherTypeDefinition
    """
    return WEATHER_REGISTRY[weather_type]


def classify_weather(tau_velocity: float, tau_half_life: float) -> List[WeatherType]:
    """
    Classify current weather conditions based on τ metrics.

    Args:
        tau_velocity: τᵥ (events/day)
        tau_half_life: τₕ (hours)

    Returns:
        List of matching weather types (may be multiple or none)
    """
    matches = []

    for weather_type, definition in WEATHER_REGISTRY.items():
        # Check τᵥ range
        if not (
            definition.tau_velocity_min
            <= tau_velocity
            <= definition.tau_velocity_max
        ):
            continue

        # Check τₕ range
        if not (
            definition.tau_half_life_min <= tau_half_life <= definition.tau_half_life_max
        ):
            continue

        matches.append(weather_type)

    return matches
