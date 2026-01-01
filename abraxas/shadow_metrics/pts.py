"""PTS - Persuasive Trajectory Score.

Tracks persuasion intensity over time.

INTERNAL USE ONLY - Access via ABX-Runes ϟ₇ operator only.
"""

from __future__ import annotations

import math
from typing import Any


def extract_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Extract PTS-specific inputs from context.

    Args:
        context: Computation context from rune invocation

    Returns:
        Inputs dict with opinion change data
    """
    symbol_pool = context.get("symbol_pool", [])
    time_window_hours = context.get("time_window_hours", 24)

    # Extract opinion metrics if available
    # Opinion change measured as aggregate shift in sentiment/stance
    opinion_values = []

    for event in symbol_pool:
        opinion = event.get("opinion_score") or event.get("stance_score")
        if opinion is not None:
            opinion_values.append(float(opinion))

    # Compute delta opinion
    if len(opinion_values) >= 2:
        # Simple delta: final - initial
        delta_opinion = opinion_values[-1] - opinion_values[0]
    elif len(opinion_values) == 1:
        # Only one value: assume no change
        delta_opinion = 0.0
    else:
        # No data: assume no change
        delta_opinion = 0.0

    # SHADOW DETECTORS: Extract optional detector results (evidence only, no influence)
    detectors = context.get("shadow_detectors", {})

    return {
        "delta_opinion": delta_opinion,
        "opinion_values": opinion_values,
        "time_window_hours": time_window_hours,
        "shadow_detectors": detectors if isinstance(detectors, dict) else {},
    }


def get_default_config() -> dict[str, Any]:
    """Get default PTS configuration.

    Returns:
        Config dict with sigmoid slope parameter
    """
    return {
        "slope_parameter": 5.0,  # Steepness of sigmoid
    }


def compute(inputs: dict[str, Any], config: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Compute PTS value.

    PTS = sigmoid(slope * Δopinion)
        = 1 / (1 + exp(-slope * Δopinion))

    Args:
        inputs: Opinion change data
        config: Configuration parameters

    Returns:
        Tuple of (PTS value [0.0, 1.0], metadata dict)
    """
    delta_opinion = inputs["delta_opinion"]
    slope = config["slope_parameter"]

    # Sigmoid function
    # Handle overflow by clamping input
    x = slope * delta_opinion
    x = max(-50, min(50, x))  # Prevent overflow

    pts = 1.0 / (1.0 + math.exp(-x))

    # Clamp to [0, 1] (should already be in range)
    pts = max(0.0, min(1.0, pts))

    metadata = {
        "delta_opinion": delta_opinion,
        "time_window_hours": inputs["time_window_hours"],
        "slope_parameter": slope,
        "opinion_values_count": len(inputs["opinion_values"]),
    }

    # SHADOW DETECTORS: Add detector evidence if present (observe only, no influence)
    detectors = inputs.get("shadow_detectors", {})
    if detectors:
        metadata["shadow_detector_evidence"] = detectors

    return pts, metadata
