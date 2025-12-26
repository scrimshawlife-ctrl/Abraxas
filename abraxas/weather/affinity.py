"""Affinity Scoring: Deterministic affinity between AAlmanac entries and weather types.

Computes affinity(term_entry, weather_type) → [0,1] based on:
- Archetype class match (SA class alignment)
- Tone alignment flags
- τ signature (velocity + half-life + phase proximity)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from abraxas.core.temporal_tau import TauSnapshot
from abraxas.weather.registry import WeatherType, WeatherTypeDefinition, WEATHER_REGISTRY


@dataclass(frozen=True)
class AffinityScore:
    """Affinity score with component breakdown."""

    total: float  # [0,1]
    archetype_match: float  # [0,1]
    tone_alignment: float  # [0,1]
    tau_signature: float  # [0,1]
    weather_type: str


def compute_affinity(
    class_id: str,
    tau_snapshot: TauSnapshot,
    tone_flags: Optional[List[str]],
    weather_type: WeatherType,
) -> AffinityScore:
    """
    Compute affinity between term entry and weather type.

    Args:
        class_id: SA class or archetype (e.g., "eggcorn", "idiom")
        tau_snapshot: τ metrics snapshot
        tone_flags: List of tone flags (e.g., ["humor", "irony"])
        weather_type: Target weather type

    Returns:
        AffinityScore with total and component scores
    """
    definition = WEATHER_REGISTRY[weather_type]

    # Component 1: Archetype class match
    archetype_match = _compute_archetype_match(class_id, definition)

    # Component 2: Tone alignment
    tone_alignment = _compute_tone_alignment(tone_flags or [], definition)

    # Component 3: τ signature
    tau_signature = _compute_tau_signature(tau_snapshot, definition)

    # Weighted combination
    # Weights: archetype=0.4, tone=0.2, tau=0.4
    total = 0.4 * archetype_match + 0.2 * tone_alignment + 0.4 * tau_signature

    return AffinityScore(
        total=total,
        archetype_match=archetype_match,
        tone_alignment=tone_alignment,
        tau_signature=tau_signature,
        weather_type=weather_type.value,
    )


def _compute_archetype_match(
    class_id: str, definition: WeatherTypeDefinition
) -> float:
    """
    Compute archetype class match score.

    Args:
        class_id: SA class or archetype
        definition: Weather type definition

    Returns:
        Match score [0,1]
    """
    # Exact match
    if class_id.lower() in [a.lower() for a in definition.archetype_affinities]:
        return 1.0

    # Partial match heuristics (deterministic)
    # Example: "eggcorn_tier1" matches "eggcorn"
    for archetype in definition.archetype_affinities:
        if archetype.lower() in class_id.lower():
            return 0.7
        if class_id.lower() in archetype.lower():
            return 0.7

    # No match
    return 0.0


def _compute_tone_alignment(
    tone_flags: List[str], definition: WeatherTypeDefinition
) -> float:
    """
    Compute tone alignment score.

    Args:
        tone_flags: List of tone flags present in entry
        definition: Weather type definition

    Returns:
        Alignment score [0,1]
    """
    if not definition.tone_flags:
        # Weather type has no tone preferences
        return 0.5

    if not tone_flags:
        # Entry has no tone flags
        return 0.3

    # Compute overlap
    tone_flags_lower = [t.lower() for t in tone_flags]
    def_flags_lower = [t.lower() for t in definition.tone_flags]

    matches = sum(1 for flag in tone_flags_lower if flag in def_flags_lower)
    max_possible = max(len(tone_flags_lower), len(def_flags_lower))

    if max_possible == 0:
        return 0.5

    return matches / max_possible


def _compute_tau_signature(
    tau_snapshot: TauSnapshot, definition: WeatherTypeDefinition
) -> float:
    """
    Compute τ signature match score.

    Args:
        tau_snapshot: τ metrics snapshot
        definition: Weather type definition

    Returns:
        Signature match score [0,1]
    """
    # Check if τᵥ is within range
    tau_v = tau_snapshot.tau_velocity
    tau_h = tau_snapshot.tau_half_life

    velocity_in_range = (
        definition.tau_velocity_min <= tau_v <= definition.tau_velocity_max
    )
    half_life_in_range = (
        definition.tau_half_life_min <= tau_h <= definition.tau_half_life_max
    )

    # Both in range: high score
    if velocity_in_range and half_life_in_range:
        return 1.0

    # One in range: medium score
    if velocity_in_range or half_life_in_range:
        return 0.5

    # Neither in range: low score (but not zero; use distance-based falloff)
    velocity_distance = min(
        abs(tau_v - definition.tau_velocity_min),
        abs(tau_v - definition.tau_velocity_max),
    )
    half_life_distance = min(
        abs(tau_h - definition.tau_half_life_min),
        abs(tau_h - definition.tau_half_life_max),
    )

    # Normalize distances (heuristic: 1.0 velocity unit = significant, 24h = significant)
    velocity_norm = max(0.0, 1.0 - velocity_distance / 2.0)
    half_life_norm = max(0.0, 1.0 - half_life_distance / 168.0)  # 7 days

    return (velocity_norm + half_life_norm) / 2.0


def compute_all_affinities(
    class_id: str,
    tau_snapshot: TauSnapshot,
    tone_flags: Optional[List[str]],
) -> Dict[WeatherType, AffinityScore]:
    """
    Compute affinities for all weather types.

    Args:
        class_id: SA class or archetype
        tau_snapshot: τ metrics snapshot
        tone_flags: List of tone flags

    Returns:
        Dict mapping WeatherType to AffinityScore
    """
    affinities = {}
    for weather_type in WeatherType:
        affinities[weather_type] = compute_affinity(
            class_id, tau_snapshot, tone_flags, weather_type
        )
    return affinities


def get_top_affinity(
    class_id: str,
    tau_snapshot: TauSnapshot,
    tone_flags: Optional[List[str]],
) -> AffinityScore:
    """
    Get highest affinity weather type.

    Args:
        class_id: SA class or archetype
        tau_snapshot: τ metrics snapshot
        tone_flags: List of tone flags

    Returns:
        AffinityScore with highest total score
    """
    affinities = compute_all_affinities(class_id, tau_snapshot, tone_flags)
    return max(affinities.values(), key=lambda a: a.total)
