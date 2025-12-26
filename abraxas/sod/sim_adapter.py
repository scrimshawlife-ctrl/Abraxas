"""SOD Simulation Adapter: Converts SML KnobVector to SOD-compatible priors.

Pure function module that bridges SML outputs to SOD scenario generation.
Does not import SOD modules directly (to avoid circular dependencies).

Returns deterministic priors that SOD can use as weights:
- Higher MRI → higher cascade branching probability
- Higher IRI → higher damping / shorter cascade length
- τ_latency/memory → lagged onset and longer tail
"""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from abraxas.sim_mappings.types import MappingResult


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


def aggregate_multi_paper_priors(mappings: List[MappingResult]) -> Dict[str, Any]:
    """
    Aggregate multiple paper mappings into a single set of SOD priors.

    Uses weighted mean aggregation where weights are derived from confidence levels:
    - HIGH confidence: weight = 1.0
    - MED confidence: weight = 0.75
    - LOW confidence: weight = 0.5

    Args:
        mappings: List of MappingResult objects from multiple papers

    Returns:
        Dict with aggregated SOD priors and provenance:
            - All standard SOD priors (same keys as convert_knobs_to_sod_priors)
            - aggregated_knobs: Weighted mean of input knobs
            - sources: List of paper IDs used in aggregation
            - weights: Per-paper confidence weights used
            - total_papers: Number of papers aggregated

    Raises:
        ValueError: If mappings list is empty

    Examples:
        >>> from abraxas.sim_mappings import map_paper_model, ModelFamily, ModelParam, PaperRef
        >>> paper1 = PaperRef("P1", "Paper 1", "http://example.com/1", None)
        >>> paper2 = PaperRef("P2", "Paper 2", "http://example.com/2", None)
        >>> params = [ModelParam("beta", value=0.3)]
        >>> mapping1 = map_paper_model(paper1, ModelFamily.DIFFUSION_SIR, params)
        >>> mapping2 = map_paper_model(paper2, ModelFamily.DIFFUSION_SIR, params)
        >>> priors = aggregate_multi_paper_priors([mapping1, mapping2])
        >>> "sources" in priors
        True
        >>> priors["total_papers"]
        2
    """
    if not mappings:
        raise ValueError("Cannot aggregate empty list of mappings")

    # Confidence to weight mapping
    confidence_weights_map = {"LOW": 0.5, "MED": 0.75, "HIGH": 1.0}

    # Accumulate weighted sums
    weighted_mri = 0.0
    weighted_iri = 0.0
    weighted_tau_latency = 0.0
    weighted_tau_memory = 0.0
    total_weight = 0.0

    # Track provenance
    sources = []
    weights = []

    for mapping in mappings:
        knobs = mapping.mapped
        confidence = knobs.confidence
        weight = confidence_weights_map.get(confidence, 0.75)

        # Accumulate weighted values
        weighted_mri += knobs.mri * weight
        weighted_iri += knobs.iri * weight
        weighted_tau_latency += knobs.tau_latency * weight
        weighted_tau_memory += knobs.tau_memory * weight
        total_weight += weight

        # Track provenance
        sources.append(mapping.paper.paper_id)
        weights.append(weight)

    # Compute weighted means
    if total_weight == 0.0:
        # All weights are zero (shouldn't happen, but handle gracefully)
        total_weight = 1.0

    aggregated_mri = weighted_mri / total_weight
    aggregated_iri = weighted_iri / total_weight
    aggregated_tau_latency = weighted_tau_latency / total_weight
    aggregated_tau_memory = weighted_tau_memory / total_weight

    # Determine aggregate confidence
    # Use maximum confidence level present in mappings
    confidence_levels = [m.mapped.confidence for m in mappings]
    if "HIGH" in confidence_levels:
        aggregate_confidence = "HIGH"
    elif "MED" in confidence_levels:
        aggregate_confidence = "MED"
    else:
        aggregate_confidence = "LOW"

    # Create aggregated knobs dict
    aggregated_knobs_dict = {
        "mri": aggregated_mri,
        "iri": aggregated_iri,
        "tau_latency": aggregated_tau_latency,
        "tau_memory": aggregated_tau_memory,
        "confidence": aggregate_confidence,
    }

    # Convert to SOD priors
    sod_priors = convert_knobs_to_sod_priors(aggregated_knobs_dict)

    # Add provenance metadata
    sod_priors["aggregated_knobs"] = {
        "mri": aggregated_mri,
        "iri": aggregated_iri,
        "tau_latency": aggregated_tau_latency,
        "tau_memory": aggregated_tau_memory,
    }
    sod_priors["sources"] = sources
    sod_priors["weights"] = weights
    sod_priors["total_papers"] = len(mappings)
    sod_priors["aggregate_confidence"] = aggregate_confidence

    return sod_priors
