"""SOD Simulation Adapter: Converts SML KnobVector to SOD-compatible priors.

Pure function module that bridges SML outputs to SOD scenario generation.
Does not import SOD modules directly (to avoid circular dependencies).

Returns deterministic priors that SOD can use as weights:
- Higher MRI → higher cascade branching probability
- Higher IRI → higher damping / shorter cascade length
- τ_latency/memory → lagged onset and longer tail
"""

from __future__ import annotations

from typing import Dict, Any


def convert_knobs_to_sod_priors(knobs_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert KnobVector (as dict) to SOD-compatible priors.

    Args:
        knobs_dict: KnobVector as dict with keys:
            - mri: float [0,1]
            - iri: float [0,1]
            - tau_latency: float [0,1]
            - tau_memory: float [0,1]
            - confidence: str

    Returns:
        Dict of SOD priors with deterministic mappings:
            - cascade_branching_prob: Higher with higher MRI
            - cascade_damping_factor: Higher with higher IRI
            - cascade_onset_lag: Higher with higher τ_latency
            - cascade_tail_length: Higher with higher τ_memory
            - confidence_weight: Scaling factor based on confidence
    """
    mri = knobs_dict.get("mri", 0.5)
    iri = knobs_dict.get("iri", 0.5)
    tau_latency = knobs_dict.get("tau_latency", 0.5)
    tau_memory = knobs_dict.get("tau_memory", 0.5)
    confidence = knobs_dict.get("confidence", "MED")

    # Confidence weights
    confidence_weights = {"LOW": 0.5, "MED": 0.75, "HIGH": 1.0}
    confidence_weight = confidence_weights.get(confidence, 0.75)

    # Cascade branching probability: Higher MRI → higher branching
    # Map [0,1] MRI to [0.2, 0.8] branching probability (scaled by confidence)
    cascade_branching_prob = 0.2 + (mri * 0.6) * confidence_weight

    # Cascade damping factor: Higher IRI → higher damping (faster decay)
    # Map [0,1] IRI to [0.1, 0.9] damping factor
    cascade_damping_factor = 0.1 + (iri * 0.8) * confidence_weight

    # Cascade onset lag: Higher τ_latency → longer delay before cascade starts
    # Map [0,1] τ_latency to [0, 48] hours
    cascade_onset_lag_hours = tau_latency * 48.0

    # Cascade tail length: Higher τ_memory → longer persistence after peak
    # Map [0,1] τ_memory to [24, 336] hours (1 day to 2 weeks)
    cascade_tail_length_hours = 24.0 + (tau_memory * 312.0)

    # Maximum cascade depth (inversely related to damping)
    # Higher damping → shallower cascade
    max_cascade_depth = int(10 * (1.0 - cascade_damping_factor))
    max_cascade_depth = max(1, max_cascade_depth)  # At least 1

    # Path probability threshold (higher MRI → easier to generate paths)
    path_probability_threshold = 0.5 - (mri * 0.3)  # [0.2, 0.5]

    return {
        "cascade_branching_prob": cascade_branching_prob,
        "cascade_damping_factor": cascade_damping_factor,
        "cascade_onset_lag_hours": cascade_onset_lag_hours,
        "cascade_tail_length_hours": cascade_tail_length_hours,
        "max_cascade_depth": max_cascade_depth,
        "path_probability_threshold": path_probability_threshold,
        "confidence_weight": confidence_weight,
        "knobs": {
            "mri": mri,
            "iri": iri,
            "tau_latency": tau_latency,
            "tau_memory": tau_memory,
        },
    }


def explain_sod_priors(priors: Dict[str, Any]) -> str:
    """
    Generate human-readable explanation of SOD priors.

    Args:
        priors: SOD priors dict from convert_knobs_to_sod_priors

    Returns:
        Human-readable explanation string
    """
    lines = [
        "SOD Priors (derived from SML knobs):",
        f"  - Cascade branching probability: {priors['cascade_branching_prob']:.2f}",
        f"  - Cascade damping factor: {priors['cascade_damping_factor']:.2f}",
        f"  - Cascade onset lag: {priors['cascade_onset_lag_hours']:.1f} hours",
        f"  - Cascade tail length: {priors['cascade_tail_length_hours']:.1f} hours",
        f"  - Max cascade depth: {priors['max_cascade_depth']}",
        f"  - Path probability threshold: {priors['path_probability_threshold']:.2f}",
        f"  - Confidence weight: {priors['confidence_weight']:.2f}",
        "",
        "Knob inputs:",
        f"  - MRI: {priors['knobs']['mri']:.2f}",
        f"  - IRI: {priors['knobs']['iri']:.2f}",
        f"  - τ_latency: {priors['knobs']['tau_latency']:.2f}",
        f"  - τ_memory: {priors['knobs']['tau_memory']:.2f}",
    ]
    return "\n".join(lines)
