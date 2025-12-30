"""ABX-Rune Operator: ϟ₄ SDS

AUTO-GENERATED OPERATOR STUB
Rune: ϟ₄ SDS — State-Dependent Susceptibility
Layer: Core
Motto: The system only resonates when the receiver is phase-open.

Canonical statement:
  Outputs are gated by receiver state; no escalation when closed.

Function:
  Gates signal reception and processing based on receiver state. Ensures that outputs are conditional on phase-alignment rather than signal strength alone.

Inputs: receiver_state, phase_alignment, incoming_signal, susceptibility_threshold
Outputs: gated_signal, reception_status, state_classification

Constraints:
  - no_escalation_when_closed; phase_alignment_required; state_must_be_measurable

Provenance:
    - EEG phase synchronization (pilot) framing
  - Schumann resonance physics corpus
  - AAL phase-gating doctrine
"""

from __future__ import annotations
from typing import Any, Dict

def apply_sds(
    state_vector: Dict[str, float],
    context: Dict[str, Any],
    interaction_kind: str = "oracle",
    susceptibility_threshold: float = 0.25,
    **kwargs: Any
) -> Dict[str, Any]:
    """Apply SDS rune operator - State-Dependent Susceptibility gating.

    Computes a susceptibility score from receiver state and determines gate status.

    Args:
        state_vector: Dict of state dimensions (arousal, coherence, openness, etc.)
                     Each value in [0.0, 1.0]. Defaults to 0.5 if missing.
        context: Contextual metadata (time_of_day, recent_history_count, etc.)
        interaction_kind: Type of interaction ("oracle", "insight", "grounding")
        susceptibility_threshold: Threshold for OPEN vs LIMINAL (default 0.25)
        **kwargs: Additional parameters (for compatibility)

    Returns:
        Dict with keys:
            - susceptibility_score: float in [0.0, 1.0]
            - gate_state: "CLOSED" | "LIMINAL" | "OPEN"
            - state_classification: dict of normalized state dimensions
            - reception_status: descriptive string
    """
    # Normalize state_vector: use defaults for missing keys
    default_dims = {
        "arousal": 0.5,
        "coherence": 0.5,
        "openness": 0.5,
        "stability": 0.5,
        "receptivity": 0.5,
    }
    normalized_state = {k: state_vector.get(k, v) for k, v in default_dims.items()}

    # Compute susceptibility score (weighted average of relevant dimensions)
    # Higher openness + receptivity + coherence → higher susceptibility
    # Lower arousal (calmer) → higher susceptibility
    weights = {
        "openness": 0.3,
        "receptivity": 0.3,
        "coherence": 0.2,
        "stability": 0.1,
        "arousal": -0.1,  # inverted: high arousal reduces susceptibility
    }

    susceptibility_score = sum(
        normalized_state.get(k, 0.5) * w for k, w in weights.items()
    )
    # Normalize to [0, 1]
    susceptibility_score = (susceptibility_score + 0.1) / 1.1
    susceptibility_score = max(0.0, min(1.0, susceptibility_score))

    # Determine gate state
    if susceptibility_score < susceptibility_threshold:
        gate_state = "CLOSED"
        reception_status = "Receiver state not phase-aligned; outputs suppressed"
    elif susceptibility_score < 0.6:
        gate_state = "LIMINAL"
        reception_status = "Partial phase-alignment; shallow outputs permitted"
    else:
        gate_state = "OPEN"
        reception_status = "Full phase-alignment; deep outputs permitted"

    return {
        "susceptibility_score": susceptibility_score,
        "gate_state": gate_state,
        "state_classification": normalized_state,
        "reception_status": reception_status,
    }
