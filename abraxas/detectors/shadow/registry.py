"""Shadow Detector Registry

Registry for shadow detectors with governance metadata.

All detectors are marked:
- mode="shadow"
- no_influence=True
- governance="emergent_candidate"

Access via ABX-Runes ϟ₇ (SSO) ONLY.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from abraxas.detectors.shadow import compliance_remix, meta_awareness, negative_space
from abraxas.detectors.shadow.types import DetectorId, DetectorValue


@dataclass(frozen=True)
class DetectorDefinition:
    """Definition for a shadow detector."""

    detector_id: DetectorId
    name: str
    description: str
    version: str
    compute_fn: Callable[[dict[str, Any], Optional[list[dict[str, Any]]], Optional[dict[str, Any]]], DetectorValue]
    mode: str = "shadow"  # Always shadow
    no_influence: bool = True  # Never influences decisions
    governance: str = "emergent_candidate"  # Subject to governance
    required_inputs: list[str] = None
    optional_inputs: list[str] = None

    def __post_init__(self):
        """Validate detector definition."""
        if not isinstance(self.required_inputs, list):
            object.__setattr__(self, "required_inputs", [])
        if not isinstance(self.optional_inputs, list):
            object.__setattr__(self, "optional_inputs", [])


# Global detector registry
DETECTOR_REGISTRY: dict[DetectorId, DetectorDefinition] = {
    DetectorId.COMPLIANCE_REMIX: DetectorDefinition(
        detector_id=DetectorId.COMPLIANCE_REMIX,
        name="Compliance vs Remix Detector",
        description=(
            "Detects balance between rote compliance/repetition and creative remix/mutation. "
            "Uses slang drift, lifecycle states, weather classification, and fog types."
        ),
        version="0.1.0",
        compute_fn=compliance_remix.compute_detector,
        mode="shadow",
        no_influence=True,
        governance="emergent_candidate",
        required_inputs=["drift_score", "lifecycle_state", "tau_velocity"],
        optional_inputs=[
            "appearances",
            "similarity_early_late",
            "new_to_window",
            "csp_ff",
            "csp_mio",
            "fog_type_counts",
            "weather_types",
            "tau_half_life",
            "observation_count",
        ],
    ),
    DetectorId.META_AWARENESS: DetectorDefinition(
        detector_id=DetectorId.META_AWARENESS,
        name="Meta-Awareness Detector",
        description=(
            "Detects meta-level discourse about manipulation, algorithms, and epistemic fatigue. "
            "Uses DMX, RDV axes, EFTE, and narrative manipulation metrics."
        ),
        version="0.1.0",
        compute_fn=meta_awareness.compute_detector,
        mode="shadow",
        no_influence=True,
        governance="emergent_candidate",
        required_inputs=["text"],
        optional_inputs=[
            "dmx_overall",
            "dmx_bucket",
            "rdv_irony",
            "rdv_humor",
            "rdv_nihilism",
            "fatigue_threshold",
            "saturation_risk",
            "rrs",
            "cis",
            "mri",
            "iri",
        ],
    ),
    DetectorId.NEGATIVE_SPACE: DetectorDefinition(
        detector_id=DetectorId.NEGATIVE_SPACE,
        name="Negative Space / Silence Detector",
        description=(
            "Detects topic dropout, visibility asymmetry, and abnormal silences. "
            "Requires history for baseline comparison. Uses symbol pool narratives and sources."
        ),
        version="0.1.0",
        compute_fn=negative_space.compute_detector,
        mode="shadow",
        no_influence=True,
        governance="emergent_candidate",
        required_inputs=["current_narratives", "baseline_narratives", "sufficient_history"],
        optional_inputs=[
            "current_sources",
            "baseline_sources",
            "source_distribution",
            "current_timestamp",
        ],
    ),
}


def get_detector_definition(detector_id: DetectorId) -> DetectorDefinition:
    """Get detector definition by ID.

    Args:
        detector_id: Detector ID enum

    Returns:
        DetectorDefinition

    Raises:
        KeyError: If detector not found
    """
    return DETECTOR_REGISTRY[detector_id]


def list_detectors() -> list[DetectorDefinition]:
    """List all registered detectors.

    Returns:
        List of detector definitions (sorted by ID)
    """
    return sorted(DETECTOR_REGISTRY.values(), key=lambda d: d.detector_id.value)


def compute_all_detectors(
    context: dict[str, Any],
    history: Optional[list[dict[str, Any]]] = None,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, DetectorValue]:
    """Compute all registered detectors.

    Args:
        context: Signal envelope context
        history: Optional history of previous envelopes
        config: Optional configuration overrides (detector-specific configs keyed by detector_id)

    Returns:
        Dict mapping detector_id to DetectorValue
    """
    results = {}

    for detector_id, definition in DETECTOR_REGISTRY.items():
        # Get detector-specific config if provided
        detector_config = None
        if config and isinstance(config, dict):
            detector_config = config.get(detector_id.value)

        # Compute detector
        try:
            value = definition.compute_fn(context, history, detector_config)
            results[detector_id.value] = value
        except Exception as e:
            # On error, return not_computable status
            # (in production, would log error)
            from abraxas.detectors.shadow.types import (
                DetectorProvenance,
                DetectorStatus,
            )
            from datetime import datetime, timezone
            from abraxas.core.provenance import hash_canonical_json

            now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            error_provenance = DetectorProvenance(
                detector_id=detector_id.value,
                used_keys=[],
                missing_keys=["error"],
                history_len=len(history) if history else 0,
                envelope_version=context.get("version"),
                inputs_hash=hash_canonical_json({}),
                config_hash=hash_canonical_json(detector_config or {}),
                computed_at_utc=now_utc,
                seed_compliant=True,
                no_influence_guarantee=True,
            )

            results[detector_id.value] = DetectorValue(
                id=detector_id,
                status=DetectorStatus.NOT_COMPUTABLE,
                value=None,
                subscores={},
                missing_keys=["error"],
                evidence={"error": str(e)},
                provenance=error_provenance,
                bounds=(0.0, 1.0),
            )

    return results


def serialize_detector_results(
    results: dict[str, DetectorValue]
) -> dict[str, Any]:
    """Serialize detector results to dict.

    Args:
        results: Dict of detector results

    Returns:
        Serialized dict (sorted keys for determinism)
    """
    serialized = {}

    for detector_id, value in sorted(results.items()):
        serialized[detector_id] = value.model_dump()

    return serialized
