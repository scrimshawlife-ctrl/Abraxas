"""ABX-Rune Operator: ϟ₆ ADD

AUTO-GENERATED OPERATOR STUB
Rune: ϟ₆ ADD — Anchor Drift Detector
Layer: Governance
Motto: When the center moves, meaning decays.

Canonical statement:
  Detect drift from the anchor; log immutably; recenter conservatively.

Function:
  Continuously monitors semantic anchor positions and detects drift. Logs drift events immutably and triggers conservative recentering when thresholds are exceeded.

Inputs: anchor_position, historical_positions, drift_threshold, entropy_metric
Outputs: drift_magnitude, drift_log_entry, recenter_signal

Constraints:
  - immutable_drift_logging; conservative_recentering; entropy_increase_detection

Provenance:
    - Drift/entropy governance principles in AAL doctrine
  - Semantic stability monitoring
  - Star Gauge / Xuanji Tu traversal logic
"""

from __future__ import annotations
from typing import Any, Dict

def apply_add(
    anchor: str,
    outputs_history: list[str],
    window: int = 20,
    drift_threshold: float = 0.7,
    **kwargs: Any
) -> Dict[str, Any]:
    """Apply ADD rune operator - Anchor Drift Detector.

    Detects semantic drift from anchor by comparing recent outputs against anchor.
    Uses simple character-level and token-level heuristics for deterministic drift detection.

    Args:
        anchor: Core semantic anchor string (motif, theme, or oracle identity)
        outputs_history: List of recent oracle output strings
        window: Number of recent outputs to analyze (default 20)
        drift_threshold: Threshold for auto-recenter trigger (default 0.7)
        **kwargs: Additional parameters (for compatibility)

    Returns:
        Dict with keys:
            - drift_magnitude: float in [0.0, 1.0] (0=stable, 1=max drift)
            - integrity_score: float in [0.0, 1.0] (1=stable, 0=degraded)
            - auto_recenter: bool (True if drift exceeds threshold)
            - analysis: dict with drift metrics
    """
    if not anchor:
        return {
            "drift_magnitude": 0.0,
            "integrity_score": 1.0,
            "auto_recenter": False,
            "analysis": {"error": "No anchor provided"},
        }

    if not outputs_history:
        return {
            "drift_magnitude": 0.0,
            "integrity_score": 1.0,
            "auto_recenter": False,
            "analysis": {"window_size": 0},
        }

    # Take last N outputs
    recent = outputs_history[-window:]

    # Compute simple drift metrics:
    # 1. Character overlap with anchor (normalized Jaccard)
    # 2. Token overlap (split on whitespace)
    # 3. Length divergence

    anchor_chars = set(anchor.lower())
    anchor_tokens = set(anchor.lower().split())
    anchor_len = len(anchor)

    char_overlaps = []
    token_overlaps = []
    len_divergences = []

    for output in recent:
        output_chars = set(output.lower())
        output_tokens = set(output.lower().split())
        output_len = len(output)

        # Jaccard similarity
        char_intersection = len(anchor_chars & output_chars)
        char_union = len(anchor_chars | output_chars)
        char_overlap = char_intersection / char_union if char_union > 0 else 0.0

        token_intersection = len(anchor_tokens & output_tokens)
        token_union = len(anchor_tokens | output_tokens)
        token_overlap = token_intersection / token_union if token_union > 0 else 0.0

        # Length divergence (normalized)
        len_div = abs(output_len - anchor_len) / max(output_len, anchor_len, 1)

        char_overlaps.append(char_overlap)
        token_overlaps.append(token_overlap)
        len_divergences.append(len_div)

    # Average metrics
    avg_char_overlap = sum(char_overlaps) / len(char_overlaps) if char_overlaps else 1.0
    avg_token_overlap = sum(token_overlaps) / len(token_overlaps) if token_overlaps else 1.0
    avg_len_div = sum(len_divergences) / len(len_divergences) if len_divergences else 0.0

    # Drift magnitude: inverse of overlap + length divergence penalty
    drift_magnitude = (1.0 - avg_char_overlap * 0.5 - avg_token_overlap * 0.5) + avg_len_div * 0.2
    drift_magnitude = max(0.0, min(1.0, drift_magnitude))

    # Integrity score: inverse of drift
    integrity_score = 1.0 - drift_magnitude

    # Auto-recenter if drift exceeds threshold
    auto_recenter = drift_magnitude >= drift_threshold

    return {
        "drift_magnitude": drift_magnitude,
        "integrity_score": integrity_score,
        "auto_recenter": auto_recenter,
        "analysis": {
            "window_size": len(recent),
            "avg_char_overlap": avg_char_overlap,
            "avg_token_overlap": avg_token_overlap,
            "avg_len_divergence": avg_len_div,
        },
    }
