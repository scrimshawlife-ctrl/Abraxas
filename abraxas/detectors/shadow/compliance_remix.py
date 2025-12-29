"""Compliance vs Remix Detector

Detects the balance between rote compliance/repetition and creative remix/mutation.

Uses real envelope fields:
- slang_drift.drift_score, appearances, csp fields
- lifecycle states (Proto, Front, Saturated, Dormant, Archived)
- weather classification (tau_velocity, tau_half_life)
- fog types (template/manufactured indicators)

SHADOW-ONLY: Feeds shadow metrics as evidence, never influences decisions.
"""

from __future__ import annotations

import socket
from datetime import datetime, timezone
from typing import Any, Optional

from abraxas.core.provenance import hash_canonical_json
from abraxas.detectors.shadow.types import (
    DetectorId,
    DetectorProvenance,
    DetectorStatus,
    DetectorValue,
    clamp01,
)


def extract_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Extract inputs from context envelope.

    Looks for real fields from slang_drift, lifecycle, weather systems.

    Args:
        context: Envelope context dict

    Returns:
        Extracted inputs dict
    """
    inputs: dict[str, Any] = {}

    # Slang drift metrics (from slang_drift.py output)
    drift_data = context.get("drift", {})
    if isinstance(drift_data, dict):
        inputs["drift_score"] = float(drift_data.get("drift_score", 0.0))
        inputs["similarity_early_late"] = float(drift_data.get("similarity_early_late", 0.0))

    # Novelty metrics
    novelty_data = context.get("novelty", {})
    if isinstance(novelty_data, dict):
        inputs["new_to_window"] = bool(novelty_data.get("new_to_window", False))

    # Appearances/repetition count
    inputs["appearances"] = int(context.get("appearances", 0))

    # CSP fields (from a2_phase term profiles)
    csp_data = context.get("csp", {})
    if isinstance(csp_data, dict):
        inputs["csp_coh"] = bool(csp_data.get("COH", False))  # Coherence
        inputs["csp_ff"] = float(csp_data.get("FF", 0.0))  # Formulaic Flag
        inputs["csp_mio"] = float(csp_data.get("MIO", 0.0))  # Manufactured Indicator Overlap

    # Lifecycle state (from lifecycle.py)
    lifecycle_state = context.get("lifecycle_state", "")
    inputs["lifecycle_state"] = str(lifecycle_state)

    # Tau metrics (from temporal_tau.py)
    tau_data = context.get("tau", {})
    if isinstance(tau_data, dict):
        inputs["tau_velocity"] = float(tau_data.get("tau_velocity", 0.0))
        inputs["tau_half_life"] = float(tau_data.get("tau_half_life", 0.0))
        inputs["observation_count"] = int(tau_data.get("observation_count", 0))

    # Fog types (from mwr_enriched fog_index)
    fog_counts = context.get("fog_type_counts", {})
    if isinstance(fog_counts, dict):
        inputs["fog_type_counts"] = dict(fog_counts)

    # Weather classification (from weather/registry.py)
    weather_types = context.get("weather_types", [])
    if isinstance(weather_types, list):
        inputs["weather_types"] = sorted([str(w) for w in weather_types])

    return inputs


def get_default_config() -> dict[str, Any]:
    """Get default configuration for detector.

    Returns:
        Config dict with weights and thresholds
    """
    return {
        "remix_weight": 0.35,
        "rote_weight": 0.30,
        "template_weight": 0.20,
        "anchor_weight": 0.15,
        # Thresholds
        "high_drift_threshold": 0.5,
        "high_repetition_threshold": 10,
        "stable_state_threshold": 0.7,  # Saturated/Dormant states
        "low_velocity_threshold": 0.1,
    }


def compute(
    inputs: dict[str, Any], config: dict[str, Any]
) -> tuple[float, dict[str, Any]]:
    """Compute Compliance vs Remix detection.

    Args:
        inputs: Extracted inputs from envelope
        config: Configuration dict

    Returns:
        Tuple of (overall_value [0,1], metadata dict)

    Higher values indicate more compliance/rote behavior.
    Lower values indicate more remix/creative mutation.
    """
    # Extract config
    remix_weight = float(config.get("remix_weight", 0.35))
    rote_weight = float(config.get("rote_weight", 0.30))
    template_weight = float(config.get("template_weight", 0.20))
    anchor_weight = float(config.get("anchor_weight", 0.15))

    high_drift_threshold = float(config.get("high_drift_threshold", 0.5))
    high_repetition_threshold = int(config.get("high_repetition_threshold", 10))
    stable_state_threshold = float(config.get("stable_state_threshold", 0.7))
    low_velocity_threshold = float(config.get("low_velocity_threshold", 0.1))

    # Initialize subscores
    remix_rate = 0.0
    rote_repetition_rate = 0.0
    template_phrase_density = 0.0
    anchor_stability = 0.0

    # --- Remix Rate ---
    # High drift + new terms + Proto/Front states = high remix
    drift_score = float(inputs.get("drift_score", 0.0))
    new_to_window = bool(inputs.get("new_to_window", False))
    lifecycle_state = str(inputs.get("lifecycle_state", ""))

    remix_rate = clamp01(drift_score)
    if new_to_window:
        remix_rate = clamp01(remix_rate + 0.2)
    if lifecycle_state in ("Proto", "Front"):
        remix_rate = clamp01(remix_rate + 0.15)

    # --- Rote Repetition Rate ---
    # High appearances + stable lifecycle + low drift = rote repetition
    appearances = int(inputs.get("appearances", 0))
    similarity_early_late = float(inputs.get("similarity_early_late", 0.0))

    if appearances >= high_repetition_threshold:
        rote_repetition_rate = clamp01(appearances / (high_repetition_threshold * 2))

    if lifecycle_state in ("Saturated", "Dormant"):
        rote_repetition_rate = clamp01(rote_repetition_rate + stable_state_threshold)

    # High similarity = low drift = rote
    rote_repetition_rate = clamp01(rote_repetition_rate + similarity_early_late * 0.3)

    # --- Template Phrase Density ---
    # CSP Formulaic Flag + fog types indicating templates
    csp_ff = float(inputs.get("csp_ff", 0.0))
    csp_mio = float(inputs.get("csp_mio", 0.0))
    fog_type_counts = inputs.get("fog_type_counts", {})

    template_phrase_density = clamp01(csp_ff)

    # MIO (Manufactured Indicator Overlap) suggests templates
    template_phrase_density = clamp01(template_phrase_density + csp_mio * 0.4)

    # Check for template-related fog types
    if isinstance(fog_type_counts, dict):
        template_fog_count = sum(
            count for fog_type, count in fog_type_counts.items()
            if "template" in str(fog_type).lower() or "manufactured" in str(fog_type).lower()
        )
        if template_fog_count > 0:
            template_phrase_density = clamp01(template_phrase_density + 0.3)

    # --- Anchor Stability ---
    # Low tau_velocity + stable weather + Saturated state = stable anchors
    tau_velocity = float(inputs.get("tau_velocity", 0.0))
    weather_types = inputs.get("weather_types", [])

    if abs(tau_velocity) < low_velocity_threshold:
        anchor_stability = 0.8
    else:
        # Inverse relationship: higher velocity = lower stability
        anchor_stability = clamp01(1.0 - abs(tau_velocity))

    # MW-02 (Compression Stability) indicates stable anchors
    if isinstance(weather_types, list) and "MW-02" in weather_types:
        anchor_stability = clamp01(anchor_stability + 0.3)

    # Saturated lifecycle = stable
    if lifecycle_state == "Saturated":
        anchor_stability = clamp01(anchor_stability + 0.2)

    # --- Overall Value ---
    # Higher value = more compliance/rote (inverse of remix)
    value = clamp01(
        rote_weight * rote_repetition_rate
        + template_weight * template_phrase_density
        + anchor_weight * anchor_stability
        + remix_weight * (1.0 - remix_rate)  # Inverse: low remix = high compliance
    )

    # Metadata
    metadata = {
        "weights": {
            "remix": remix_weight,
            "rote": rote_weight,
            "template": template_weight,
            "anchor": anchor_weight,
        },
        "subscores": {
            "remix_rate": remix_rate,
            "rote_repetition_rate": rote_repetition_rate,
            "template_phrase_density": template_phrase_density,
            "anchor_stability": anchor_stability,
        },
        "lifecycle_state": lifecycle_state,
        "drift_score": drift_score,
        "appearances": appearances,
    }

    return value, metadata


def compute_detector(
    context: dict[str, Any],
    history: Optional[list[dict[str, Any]]] = None,
    config: Optional[dict[str, Any]] = None,
) -> DetectorValue:
    """Compute Compliance vs Remix detector value.

    Args:
        context: Signal envelope context
        history: Optional history of previous envelopes (not used for this detector)
        config: Optional configuration overrides

    Returns:
        DetectorValue with status, value, subscores, provenance
    """
    # Extract inputs
    inputs = extract_inputs(context)

    # Use provided config or defaults
    detector_config = config or get_default_config()

    # Determine which keys were used and which are missing
    # CRITICAL: Check source data, not just extracted inputs (which may have defaults)
    required_keys = ["drift_score", "lifecycle_state", "tau_velocity"]
    optional_keys = [
        "appearances",
        "similarity_early_late",
        "new_to_window",
        "csp_ff",
        "csp_mio",
        "fog_type_counts",
        "weather_types",
        "tau_half_life",
        "observation_count",
    ]

    # Check if required data exists in source context
    missing_keys = []
    if "drift" not in context or not isinstance(context.get("drift"), dict):
        missing_keys.append("drift_score")
    elif "drift_score" not in context["drift"]:
        missing_keys.append("drift_score")

    if "lifecycle_state" not in context or not context.get("lifecycle_state"):
        missing_keys.append("lifecycle_state")

    if "tau" not in context or not isinstance(context.get("tau"), dict):
        missing_keys.append("tau_velocity")
    elif "tau_velocity" not in context["tau"]:
        missing_keys.append("tau_velocity")

    missing_keys = sorted(missing_keys)

    used_keys = sorted([k for k in required_keys + optional_keys if k not in missing_keys and k in inputs])

    # Compute status
    status = DetectorStatus.OK if not missing_keys else DetectorStatus.NOT_COMPUTABLE

    # Compute value if status is OK
    value: Optional[float] = None
    subscores: dict[str, float] = {}
    evidence: Optional[dict[str, Any]] = None

    if status == DetectorStatus.OK:
        computed_value, metadata = compute(inputs, detector_config)
        value = computed_value
        subscores = {
            "remix_rate": clamp01(metadata["subscores"]["remix_rate"]),
            "rote_repetition_rate": clamp01(metadata["subscores"]["rote_repetition_rate"]),
            "template_phrase_density": clamp01(metadata["subscores"]["template_phrase_density"]),
            "anchor_stability": clamp01(metadata["subscores"]["anchor_stability"]),
        }
        evidence = metadata if metadata else None

    # Create provenance
    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    provenance = DetectorProvenance(
        detector_id=DetectorId.COMPLIANCE_REMIX.value,
        used_keys=used_keys,
        missing_keys=missing_keys,
        history_len=len(history) if history else 0,
        envelope_version=context.get("version"),
        inputs_hash=hash_canonical_json(inputs),
        config_hash=hash_canonical_json(detector_config),
        computed_at_utc=now_utc,
        seed_compliant=True,
        no_influence_guarantee=True,
    )

    return DetectorValue(
        id=DetectorId.COMPLIANCE_REMIX,
        status=status,
        value=value,
        subscores=subscores,
        missing_keys=missing_keys,
        evidence=evidence,
        provenance=provenance,
        bounds=(0.0, 1.0),
    )
