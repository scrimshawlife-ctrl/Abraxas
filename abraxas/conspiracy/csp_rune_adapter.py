"""Rune adapter for conspiracy CSP (Coordination Signal Proxy) computation capability.

Thin adapter layer exposing conspiracy.csp.compute_term via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.conspiracy.csp import compute_term_csp as compute_term_csp_core


def compute_term_csp_deterministic(
    term: str,
    profile: Dict[str, Any],
    dmx_bucket: str,
    dmx_overall: float,
    term_class: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term CSP computation.

    Wraps existing compute_term_csp with provenance envelope.

    Args:
        term: Term string (for COH inference)
        profile: A2 profile dict with attribution, diversity, consensus metrics
        dmx_bucket: DMX bucket (LOW/MED/HIGH)
        dmx_overall: Overall manipulation risk [0,1]
        term_class: Term classification (stable/emerging/contested/volatile/unknown)
        seed: Optional deterministic seed (kept for consistency)

    Returns:
        Dictionary with csp_result, success status, and provenance
    """
    # Validate inputs
    missing = []
    if not isinstance(term, str):
        missing.append("term")
    if not isinstance(profile, dict):
        missing.append("profile")
    if not isinstance(dmx_bucket, str):
        missing.append("dmx_bucket")
    if not isinstance(dmx_overall, (int, float)):
        missing.append("dmx_overall")
    if not isinstance(term_class, str):
        missing.append("term_class")

    if missing:
        return {
            "success": False,
            "csp_result": None,
            "not_computable": {
                "reason": f"Invalid inputs: {', '.join(missing)}",
                "missing_inputs": missing
            },
            "provenance": None
        }

    # Call existing compute_term_csp function (pure, deterministic)
    try:
        csp_result = compute_term_csp_core(
            term=term,
            profile=profile,
            dmx_bucket=dmx_bucket,
            dmx_overall=float(dmx_overall),
            term_class=term_class
        )
    except Exception as e:
        # Not computable - return structured error
        return {
            "success": False,
            "csp_result": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"success": True, "csp_result": csp_result},
        config={},
        inputs={
            "term": term,
            "profile": profile,
            "dmx_bucket": dmx_bucket,
            "dmx_overall": dmx_overall,
            "term_class": term_class
        },
        operation_id="conspiracy.csp.compute_term",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "success": True,
        "csp_result": csp_result,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["compute_term_csp_deterministic"]
