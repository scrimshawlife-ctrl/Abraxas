"""
Resonance Narratives Rendering Rules v1

Defines hard constraints for narrative generation:
- Allowed JSON pointers (whitelist)
- Required fields mapping
- Forbidden causal phrases without evidence
"""

from typing import Set, Dict, List

# Whitelisted JSON pointers that the renderer may reference
# This prevents hallucination by explicitly allowing only known envelope paths
ALLOWED_POINTERS: Set[str] = {
    # Window information
    "/oracle_signal/window/start_iso",
    "/oracle_signal/window/end_iso",
    "/oracle_signal/window/bucket",

    # V1 scores - Slang
    "/oracle_signal/scores_v1/slang/top_vital",
    "/oracle_signal/scores_v1/slang/top_risk",
    "/oracle_signal/scores_v1/slang/vital_count",
    "/oracle_signal/scores_v1/slang/risk_count",

    # V1 scores - AAlmanac
    "/oracle_signal/scores_v1/aalmanac/top_patterns",
    "/oracle_signal/scores_v1/aalmanac/pattern_count",

    # V2 compliance and mode
    "/oracle_signal/v2/mode",
    "/oracle_signal/v2/compliance/status",
    "/oracle_signal/v2/compliance/provenance/config_hash",
    "/oracle_signal/v2/compliance/evidence_budget_bytes",
    "/oracle_signal/v2/compliance/checks",

    # V2 scores (if present)
    "/oracle_signal/v2/scores_v2/signal_layer/motifs",
    "/oracle_signal/v2/scores_v2/signal_layer/resonance_score",
    "/oracle_signal/v2/scores_v2/signal_layer/drift_velocity",
    "/oracle_signal/v2/scores_v2/forecast_layer/phase_transitions",
    "/oracle_signal/v2/scores_v2/forecast_layer/weather_trajectory",
    "/oracle_signal/v2/scores_v2/forecast_layer/memetic_pressure",

    # Evidence (if present)
    "/oracle_signal/evidence/paths",
    "/oracle_signal/evidence/hashes",

    # Meta information
    "/oracle_signal/meta/source_count",
    "/oracle_signal/meta/run_id",
    "/oracle_signal/meta/created_at",
}

# Required fields mapping: if envelope contains X, narrative must include summary line Y
REQUIRED_IF_PRESENT: Dict[str, str] = {
    "/oracle_signal/v2/compliance/status": "Compliance status in signal_summary",
    "/oracle_signal/window/start_iso": "Time window in signal_summary",
    "/oracle_signal/scores_v1/slang/top_vital": "Top vital slang terms in signal_summary or motifs",
}

# Forbidden causal phrases unless accompanied by evidence pointer
# These prevent the renderer from making unsupported causal claims
FORBIDDEN_PHRASES_WITHOUT_EVIDENCE: List[str] = [
    "because",
    "caused by",
    "this means",
    "therefore",
    "as a result",
    "consequently",
    "due to",
    "leads to",
    "resulting in",
]

# Allowed overlay types for overlay_notes
ALLOWED_OVERLAY_TYPES: Set[str] = {
    "WARNING",
    "CONTEXT",
    "ADVISORY",
    "CLARIFICATION",
    "LIMITATION",
}


def is_pointer_allowed(pointer: str) -> bool:
    """
    Check if a JSON pointer is whitelisted for rendering.

    Args:
        pointer: JSON pointer string (e.g., "/oracle_signal/window/start_iso")

    Returns:
        True if pointer is in whitelist, False otherwise
    """
    return pointer in ALLOWED_POINTERS


def validate_narrative_text(text: str, has_evidence: bool) -> List[str]:
    """
    Validate narrative text against forbidden phrases rule.

    Args:
        text: Narrative text to validate
        has_evidence: Whether evidence pointers are present in envelope

    Returns:
        List of validation warnings (empty if valid)
    """
    warnings: List[str] = []

    if not has_evidence:
        text_lower = text.lower()
        for phrase in FORBIDDEN_PHRASES_WITHOUT_EVIDENCE:
            if phrase in text_lower:
                warnings.append(
                    f"Causal phrase '{phrase}' used without evidence support"
                )

    return warnings


def validate_overlay_type(overlay_type: str) -> bool:
    """
    Check if overlay type is allowed.

    Args:
        overlay_type: Type of overlay annotation

    Returns:
        True if overlay type is allowed, False otherwise
    """
    return overlay_type in ALLOWED_OVERLAY_TYPES
