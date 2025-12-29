"""NOR - Narrative Overload Rating.

Detects narrative saturation and competing storylines.

INTERNAL USE ONLY - Access via ABX-Runes ϟ₇ operator only.
"""

from __future__ import annotations

import math
from typing import Any


def extract_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Extract NOR-specific inputs from context.

    Args:
        context: Computation context from rune invocation

    Returns:
        Inputs dict with narrative data
    """
    symbol_pool = context.get("symbol_pool", [])

    # Extract unique narrative IDs
    narrative_ids = set()

    for event in symbol_pool:
        # Narratives may be stored as tags, topics, or explicit IDs
        narrative = event.get("narrative_id") or event.get("topic") or event.get("theme")
        if narrative:
            narrative_ids.add(str(narrative))

    # SHADOW DETECTORS: Extract optional detector results (evidence only, no influence)
    detectors = context.get("shadow_detectors", {})

    return {
        "narrative_ids": sorted(narrative_ids),  # Sorted for determinism
        "narrative_count": len(narrative_ids),
        "shadow_detectors": detectors if isinstance(detectors, dict) else {},
    }


def get_default_config() -> dict[str, Any]:
    """Get default NOR configuration.

    Returns:
        Config dict with decay parameter
    """
    return {
        "decay_constant": 0.3,  # λ in saturation function
    }


def compute(inputs: dict[str, Any], config: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Compute NOR value.

    NOR = 1 - exp(-λ * narrative_count)

    This is a saturation function that approaches 1.0 as narrative count increases.

    Args:
        inputs: Narrative data
        config: Configuration parameters

    Returns:
        Tuple of (NOR value [0.0, 1.0], metadata dict)
    """
    narrative_count = inputs["narrative_count"]
    lambda_decay = config["decay_constant"]

    # Saturation function
    nor = 1.0 - math.exp(-lambda_decay * narrative_count)

    # Clamp to [0, 1] (should already be in range, but safety)
    nor = max(0.0, min(1.0, nor))

    metadata = {
        "narrative_count": narrative_count,
        "decay_constant": lambda_decay,
        "narrative_ids": inputs["narrative_ids"],
    }

    # SHADOW DETECTORS: Add detector evidence if present (observe only, no influence)
    detectors = inputs.get("shadow_detectors", {})
    if detectors:
        metadata["shadow_detector_evidence"] = detectors

    return nor, metadata
