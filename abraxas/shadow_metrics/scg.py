"""SCG - Social Contagion Gradient.

Measures rate of social transmission and viral potential.

INTERNAL USE ONLY - Access via ABX-Runes ϟ₇ operator only.
"""

from __future__ import annotations

from typing import Any


def extract_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Extract SCG-specific inputs from context.

    Args:
        context: Computation context from rune invocation

    Returns:
        Inputs dict with transmission data
    """
    symbol_pool = context.get("symbol_pool", [])
    time_window_hours = context.get("time_window_hours", 24)

    # Extract transmission events
    # Each event may have exposure count and transmission count
    total_exposed = 0
    total_transmitted = 0

    for event in symbol_pool:
        exposed = event.get("exposed_count", 0)
        transmitted = event.get("transmission_count", 0) or event.get("share_count", 0)

        total_exposed += exposed
        total_transmitted += transmitted

    # Estimate effective reproduction number R
    # R = average number of secondary transmissions per exposure
    if total_exposed > 0:
        r_effective = total_transmitted / total_exposed
    else:
        r_effective = 0.0

    return {
        "r_effective": r_effective,
        "total_exposed": total_exposed,
        "total_transmitted": total_transmitted,
        "time_window_hours": time_window_hours,
    }


def get_default_config() -> dict[str, Any]:
    """Get default SCG configuration.

    Returns:
        Config dict with R_max parameter
    """
    return {
        "r_max": 10.0,  # Maximum R for normalization
    }


def compute(inputs: dict[str, Any], config: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Compute SCG value.

    SCG = (R_effective - 1) / (R_max - 1)

    This normalizes R to [0, 1] where:
    - R = 1 → SCG ≈ 0.0 (critical threshold)
    - R < 1 → SCG < 0.0 (sub-critical, clamped to 0)
    - R > 1 → SCG > 0.0 (super-critical)
    - R = R_max → SCG = 1.0

    Args:
        inputs: Transmission data
        config: Configuration parameters

    Returns:
        Tuple of (SCG value [0.0, 1.0], metadata dict)
    """
    r_effective = inputs["r_effective"]
    r_max = config["r_max"]

    # Normalize R
    scg = (r_effective - 1.0) / (r_max - 1.0)

    # Clamp to [0, 1]
    scg = max(0.0, min(1.0, scg))

    metadata = {
        "r_effective": r_effective,
        "r_max": r_max,
        "observation_window_hours": inputs["time_window_hours"],
        "total_exposed": inputs["total_exposed"],
        "total_transmitted": inputs["total_transmitted"],
    }

    return scg, metadata
