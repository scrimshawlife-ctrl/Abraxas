"""Rune adapter for conspiracy capabilities.

Thin adapter layer exposing abraxas.conspiracy.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.conspiracy.csp import (
    compute_claim_csp as compute_claim_csp_core,
    compute_term_csp as compute_term_csp_core
)
from abraxas.conspiracy.policy import (
    csp_horizon_clamp as csp_horizon_clamp_core,
    apply_horizon_cap as apply_horizon_cap_core
)


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
    Rune-compatible term CSP calculator.

    Wraps existing compute_term_csp with provenance envelope.
    Computes Conspiracy Susceptibility Profile (CSP) for terms.

    Args:
        term: Term string (used for COH inference heuristic)
        profile: Term profile dictionary with metrics
        dmx_bucket: DMX manipulation risk bucket (LOW/MED/HIGH/UNKNOWN)
        dmx_overall: Overall DMX manipulation risk score [0, 1]
        term_class: Term classification string
        seed: Optional deterministic seed

    Returns:
        Dictionary with term_csp dict, provenance, and not_computable (always None)
    """
    # Call existing compute_term_csp function (no changes to core logic)
    term_csp = compute_term_csp_core(
        term=term,
        profile=profile,
        dmx_bucket=dmx_bucket,
        dmx_overall=dmx_overall,
        term_class=term_class
    )

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"term_csp": term_csp},
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
        "term_csp": term_csp,
        "provenance": envelope["provenance"],
        "not_computable": None  # CSP computation never fails
    }


def csp_horizon_clamp_deterministic(
    csp: Dict[str, Any],
    dmx_bucket: str,
    term_class: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible CSP horizon clamp.

    Wraps existing csp_horizon_clamp with provenance envelope.
    Returns horizon cap and flags based on CSP metrics and DMX context.

    Args:
        csp: Conspiracy Susceptibility Profile dict (MIO, FF, EA, CIP, COH)
        dmx_bucket: DMX manipulation risk bucket (LOW, MED, HIGH, UNKNOWN)
        term_class: Term classification (stable, contested, volatile, unknown)
        seed: Optional deterministic seed (unused for clamping, kept for consistency)

    Returns:
        Dictionary with cap (str|null), flags (list), provenance, and not_computable (always None)
    """
    # Call existing csp_horizon_clamp function (returns tuple: cap, flags)
    cap, flags = csp_horizon_clamp_core(
        csp=csp,
        dmx_bucket=dmx_bucket,
        term_class=term_class
    )

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"cap": cap, "flags": flags},
        config={},
        inputs={"csp": csp, "dmx_bucket": dmx_bucket, "term_class": term_class},
        operation_id="conspiracy.policy.horizon_clamp",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "cap": cap,
        "flags": flags,
        "provenance": envelope["provenance"],
        "not_computable": None  # clamping never fails
    }


def apply_horizon_cap_deterministic(
    policy_cap: Optional[str],
    csp_cap: Optional[str],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible horizon cap application.

    Wraps existing apply_horizon_cap with provenance envelope.
    Returns minimum of policy_cap and csp_cap (most restrictive).

    Args:
        policy_cap: Policy-based horizon cap (days, weeks, months, years) or null
        csp_cap: CSP-based horizon cap or null
        seed: Optional deterministic seed (unused for cap application, kept for consistency)

    Returns:
        Dictionary with final_cap (str|null), provenance, and not_computable (always None)
    """
    # Call existing apply_horizon_cap function (returns Optional[str])
    final_cap = apply_horizon_cap_core(
        policy_cap=policy_cap,
        csp_cap=csp_cap
    )

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"final_cap": final_cap},
        config={},
        inputs={"policy_cap": policy_cap, "csp_cap": csp_cap},
        operation_id="conspiracy.policy.apply_cap",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "final_cap": final_cap,
        "provenance": envelope["provenance"],
        "not_computable": None  # cap application never fails
    }


__all__ = [
    "compute_claim_csp_deterministic",
    "compute_term_csp_deterministic",
    "csp_horizon_clamp_deterministic",
    "apply_horizon_cap_deterministic"
]
