"""
Rune adapter for drift capabilities.

Provides deterministic capability wrappers for drift detection functions with SEED compliance.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope, ProvenanceBundle
from abraxas.drift.orchestrator import analyze_text_for_drift as analyze_text_for_drift_core


def analyze_text_for_drift_deterministic(
    text: str,
    provenance: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Deterministic wrapper for analyze_text_for_drift with provenance tracking.

    Args:
        text: The text to analyze for drift indicators
        provenance: ProvenanceBundle as dict (inputs, transforms, metadata)
        seed: Optional seed for SEED compliance (unused, for consistency)
        **kwargs: Additional arguments (captured for provenance)

    Returns:
        Dict with keys:
            - drift_report (dict): DriftReport with text_sha256, provenance, flags, notes
            - provenance (dict): SHA-256 provenance envelope for this invocation
            - not_computable (None): Always None for this capability
    """
    # Reconstruct ProvenanceBundle from dict
    provenance_bundle = ProvenanceBundle(**provenance)

    # Call core function
    drift_report_obj = analyze_text_for_drift_core(text, provenance_bundle)

    # Convert DriftReport to dict
    drift_report = drift_report_obj.model_dump()

    # Build provenance envelope
    inputs_dict = {
        "text": text,
        "provenance": provenance,
    }
    config_dict = {
        "seed": seed,
        **kwargs
    }

    envelope = canonical_envelope(
        inputs=inputs_dict,
        outputs={"drift_report": drift_report},
        config=config_dict,
        errors=None
    )

    return {
        "drift_report": drift_report,
        "provenance": envelope["provenance"],
        "not_computable": None
    }
