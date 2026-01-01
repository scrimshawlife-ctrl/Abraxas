"""SML Mapper: Core mapping logic from model parameters to Abraxas knobs.

Implements:
- map_params_to_knobs: Map list of parameters to KnobVector
- map_paper_model: Complete mapping with paper metadata
"""

from __future__ import annotations

from typing import List

from abraxas.sim_mappings.types import (
    ModelFamily,
    ModelParam,
    KnobVector,
    MappingResult,
    PaperRef,
)
from abraxas.sim_mappings.normalizers import (
    minmax_clip,
    evidence_completeness,
    safe_mean,
)
from abraxas.sim_mappings.family_maps import (
    get_family_key_params,
    get_mri_params,
    get_iri_params,
    get_tau_params,
    get_param_range,
    is_inverted_param,
)


def map_params_to_knobs(
    family: ModelFamily,
    params: List[ModelParam],
) -> KnobVector:
    """
    Map model parameters to Abraxas KnobVector.

    Args:
        family: Model family (determines mapping rules)
        params: List of model parameters with values

    Returns:
        KnobVector with mapped MRI, IRI, τ components and confidence
    """
    # Create param lookup dict
    param_dict = {p.name: p for p in params}

    # Get family-specific param lists
    mri_param_names = get_mri_params(family)
    iri_param_names = get_iri_params(family)
    tau_param_names = get_tau_params(family)
    key_param_names = get_family_key_params(family)

    # Compute evidence completeness
    completeness, confidence = evidence_completeness(
        params, key_param_names, require_numeric=True
    )

    # Map MRI components
    mri_values = []
    mri_contributors = []
    for param_name in mri_param_names:
        if param_name in param_dict:
            param = param_dict[param_name]
            if param.value is not None:
                lo, hi = get_param_range(param_name)
                inverted = is_inverted_param(param_name)

                normalized = minmax_clip(param.value, lo, hi)
                if inverted:
                    normalized = 1.0 - normalized  # Invert

                mri_values.append(normalized)
                symbol = param.symbol or param_name
                mri_contributors.append(symbol)

    mri = safe_mean(mri_values, default=0.5)

    # Map IRI components
    iri_values = []
    iri_contributors = []
    for param_name in iri_param_names:
        if param_name in param_dict:
            param = param_dict[param_name]
            if param.value is not None:
                lo, hi = get_param_range(param_name)
                normalized = minmax_clip(param.value, lo, hi)

                iri_values.append(normalized)
                symbol = param.symbol or param_name
                iri_contributors.append(symbol)

    iri = safe_mean(iri_values, default=0.5)

    # Map τ components
    tau_latency_values = []
    tau_memory_values = []
    tau_contributors = []

    for param_name in tau_param_names:
        if param_name in param_dict:
            param = param_dict[param_name]
            if param.value is not None:
                lo, hi = get_param_range(param_name)
                normalized = minmax_clip(param.value, lo, hi)

                # Heuristic: delay-like params contribute to latency,
                # memory/kernel params contribute to memory
                if "delay" in param_name.lower() or "lag" in param_name.lower():
                    tau_latency_values.append(normalized)
                elif "memory" in param_name.lower() or "kernel" in param_name.lower():
                    tau_memory_values.append(normalized)
                else:
                    # Generic temporal param: contribute to both
                    tau_latency_values.append(normalized)
                    tau_memory_values.append(normalized)

                symbol = param.symbol or param_name
                tau_contributors.append(symbol)

    tau_latency = safe_mean(tau_latency_values, default=0.5)
    tau_memory = safe_mean(tau_memory_values, default=0.5)

    # Build explanation
    explanation_parts = []
    if mri_contributors:
        explanation_parts.append(f"MRI from {', '.join(mri_contributors)}")
    if iri_contributors:
        explanation_parts.append(f"IRI from {', '.join(iri_contributors)}")
    if tau_contributors:
        explanation_parts.append(f"τ from {', '.join(tau_contributors)}")

    if not explanation_parts:
        explanation = f"No numeric params found for {family.value}"
    else:
        explanation = "; ".join(explanation_parts)

    return KnobVector(
        mri=mri,
        iri=iri,
        tau_latency=tau_latency,
        tau_memory=tau_memory,
        confidence=confidence,
        explanation=explanation,
    )


def map_paper_model(
    paper: PaperRef,
    family: ModelFamily,
    params: List[ModelParam],
) -> MappingResult:
    """
    Complete mapping from paper model to Abraxas knobs.

    Args:
        paper: Paper reference
        family: Model family
        params: List of model parameters

    Returns:
        MappingResult with complete mapping and component breakdown
    """
    # Map to knobs
    knobs = map_params_to_knobs(family, params)

    # Build component breakdown
    param_dict = {p.name: p for p in params}
    mri_param_names = get_mri_params(family)
    iri_param_names = get_iri_params(family)
    tau_param_names = get_tau_params(family)

    mri_components = []
    for param_name in mri_param_names:
        if param_name in param_dict and param_dict[param_name].value is not None:
            symbol = param_dict[param_name].symbol or param_name
            mri_components.append(symbol)

    iri_components = []
    for param_name in iri_param_names:
        if param_name in param_dict and param_dict[param_name].value is not None:
            symbol = param_dict[param_name].symbol or param_name
            iri_components.append(symbol)

    tau_components = []
    for param_name in tau_param_names:
        if param_name in param_dict and param_dict[param_name].value is not None:
            symbol = param_dict[param_name].symbol or param_name
            tau_components.append(symbol)

    mapped_components = {
        "MRI": mri_components,
        "IRI": iri_components,
        "τ": tau_components,
    }

    return MappingResult(
        paper=paper,
        family=family,
        params=params,
        mapped=knobs,
        mapped_components=mapped_components,
    )
