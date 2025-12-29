"""FVC - Filter Velocity Coefficient.

Tracks speed of information filtering and echo chamber formation.

INTERNAL USE ONLY - Access via ABX-Runes ϟ₇ operator only.
"""

from __future__ import annotations

from typing import Any


def extract_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Extract FVC-specific inputs from context.

    Args:
        context: Computation context from rune invocation

    Returns:
        Inputs dict with source diversity data
    """
    symbol_pool = context.get("symbol_pool", [])

    # Extract sources and their counts
    source_counts: dict[str, int] = {}

    for event in symbol_pool:
        source = event.get("source") or event.get("origin") or "unknown"
        source = str(source)
        source_counts[source] = source_counts.get(source, 0) + 1

    # Compute proportions
    total = sum(source_counts.values())
    source_distribution = {}

    if total > 0:
        for source, count in source_counts.items():
            source_distribution[source] = count / total
    else:
        source_distribution = {}

    # SHADOW DETECTORS: Extract optional detector results (evidence only, no influence)
    detectors = context.get("shadow_detectors", {})

    return {
        "source_distribution": source_distribution,
        "source_count": len(source_counts),
        "total_events": total,
        "shadow_detectors": detectors if isinstance(detectors, dict) else {},
    }


def get_default_config() -> dict[str, Any]:
    """Get default FVC configuration.

    Returns:
        Empty config (no parameters needed)
    """
    return {}


def compute(inputs: dict[str, Any], config: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Compute FVC value.

    FVC = 1 - diversity_index

    where diversity_index = Simpson's diversity index:
    D = 1 - Σ(p_i^2) for each source proportion p_i

    Higher FVC → Lower diversity → More filtering

    Args:
        inputs: Source diversity data
        config: Configuration parameters

    Returns:
        Tuple of (FVC value [0.0, 1.0], metadata dict)
    """
    source_distribution = inputs["source_distribution"]

    # Handle edge case: no sources
    if not source_distribution:
        return 0.0, {
            "diversity_index": 0.0,
            "source_count": 0,
            "source_distribution": {},
        }

    # Compute Simpson's diversity index
    # D = 1 - Σ(p_i^2)
    sum_squares = sum(p**2 for p in source_distribution.values())
    diversity_index = 1.0 - sum_squares

    # FVC = 1 - diversity
    # High diversity (D ≈ 1) → Low filtering (FVC ≈ 0)
    # Low diversity (D ≈ 0) → High filtering (FVC ≈ 1)
    fvc = 1.0 - diversity_index

    # Clamp to [0, 1] (should already be in range)
    fvc = max(0.0, min(1.0, fvc))

    metadata = {
        "diversity_index": diversity_index,
        "source_count": inputs["source_count"],
        "source_distribution": {
            k: round(v, 4) for k, v in sorted(source_distribution.items())
        },
    }

    # SHADOW DETECTORS: Add detector evidence if present (observe only, no influence)
    detectors = inputs.get("shadow_detectors", {})
    if detectors:
        metadata["shadow_detector_evidence"] = detectors

    return fvc, metadata
