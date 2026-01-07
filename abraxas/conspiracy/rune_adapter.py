"""Rune adapter for conspiracy capabilities.

Thin adapter layer exposing abraxas.conspiracy.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.conspiracy.csp import compute_claim_csp as compute_claim_csp_core


def compute_claim_csp_deterministic(
    claim_text: str,
    term_csp: Dict[str, Any],
    evidence_support_weight: float = 0.0,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible claim CSP calculator.

    Wraps existing compute_claim_csp with provenance envelope.
    Computes Conspiracy Susceptibility Profile (CSP) for claims.

    Args:
        claim_text: Claim text to analyze for CSP computation
        term_csp: Base term-level CSP (from compute_term_csp or empty dict)
        evidence_support_weight: Evidence support weight bonus [0, 1] (default: 0.0)
        seed: Optional deterministic seed (unused for computation, kept for consistency)

    Returns:
        Dictionary with claim_csp dict, provenance, and not_computable (always None)
    """
    # Call existing compute_claim_csp function (no changes to core logic)
    claim_csp = compute_claim_csp_core(
        claim_text=claim_text,
        term_csp=term_csp,
        evidence_support_weight=evidence_support_weight
    )

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"claim_csp": claim_csp},
        config={"evidence_support_weight": evidence_support_weight},
        inputs={"claim_text": claim_text, "term_csp": term_csp},
        operation_id="conspiracy.csp.compute_claim",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "claim_csp": claim_csp,
        "provenance": envelope["provenance"],
        "not_computable": None  # CSP computation never fails, returns default values on error
    }


__all__ = [
    "compute_claim_csp_deterministic"
]
