"""Rune gating and window scheduling for oracle outputs."""
from __future__ import annotations
from typing import Any, Dict

from abraxas.runes.operators.sds import apply_sds
from abraxas.runes.operators.ipl import apply_ipl


def compute_gate(
    state_vector: Dict[str, float],
    context: Dict[str, Any],
    interaction_kind: str = "oracle"
) -> Dict[str, Any]:
    """Compute SDS gate state from receiver state.

    Args:
        state_vector: Dict of state dimensions (arousal, coherence, openness, etc.)
        context: Contextual metadata
        interaction_kind: Type of interaction ("oracle", "insight", "grounding")

    Returns:
        SDS gate bundle with keys: susceptibility_score, gate_state, etc.
    """
    return apply_sds(
        state_vector=state_vector,
        context=context,
        interaction_kind=interaction_kind
    )


def enforce_depth(gate_bundle: Dict[str, Any], requested_depth: str) -> str:
    """Map gate state to permitted depth level.

    Args:
        gate_bundle: Output from compute_gate
        requested_depth: User-requested depth ("grounding" | "shallow" | "deep")

    Returns:
        Effective depth string based on gate state:
            CLOSED -> "grounding"
            LIMINAL -> "shallow"
            OPEN -> requested_depth (honored as-is)
    """
    gate_state = gate_bundle.get("gate_state", "CLOSED")

    if gate_state == "CLOSED":
        return "grounding"
    elif gate_state == "LIMINAL":
        return "shallow"
    else:  # OPEN
        return requested_depth


def schedule_insight_window(
    phase_series: list[tuple[float, float]] | None,
    gate_bundle: Dict[str, Any],
    window_s: float = 2.0,
    lock_threshold: float = 0.35,
    refractory_s: float = 8.0
) -> Dict[str, Any]:
    """Schedule IPL windows if gate is OPEN.

    Args:
        phase_series: List of (timestamp, phase_value) tuples or None
        gate_bundle: Output from compute_gate
        window_s: Window duration in seconds (default 2.0)
        lock_threshold: Phase coherence threshold (default 0.35)
        refractory_s: Refractory period in seconds (default 8.0)

    Returns:
        IPL schedule bundle with keys: events, total_windows, lock_status, etc.
        If gate is not OPEN, returns empty schedule.
    """
    gate_state = gate_bundle.get("gate_state", "CLOSED")

    if gate_state != "OPEN":
        return {
            "events": [],
            "total_windows": 0,
            "refractory_enforced": True,
            "lock_status": "inactive",
            "reason": f"Gate not OPEN (state={gate_state})"
        }

    return apply_ipl(
        phase_series=phase_series,
        gate_bundle=gate_bundle,
        window_s=window_s,
        lock_threshold=lock_threshold,
        refractory_s=refractory_s
    )
