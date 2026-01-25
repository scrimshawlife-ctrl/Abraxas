"""
Rune adapter for core capabilities.

Provides deterministic capability wrappers for core Abraxas functions with SEED compliance.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.core.rendering import render_output as render_output_core
from abraxas.fn_exports import EXPORTS, NOW


def render_output_deterministic(
    draft_text: str,
    context: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Deterministic wrapper for render_output with provenance tracking.

    Args:
        draft_text: The draft text to render
        context: Optional context dict (intent, frame_id, etc.)
        seed: Optional seed for SEED compliance (unused, for consistency)
        **kwargs: Additional arguments (captured for provenance)

    Returns:
        Dict with keys:
            - rendered_text (str): The rendered text (unchanged from draft)
            - provenance (dict): SHA-256 provenance envelope
            - not_computable (None): Always None for this capability
    """
    # Call core function
    rendered_text = render_output_core(draft_text, context=context or {})

    # Build provenance envelope
    inputs_dict = {
        "draft_text": draft_text,
        "context": context or {},
    }
    config_dict = {
        "seed": seed,
        **kwargs
    }

    envelope = canonical_envelope(
        result={"rendered_text": rendered_text},
        config=config_dict,
        inputs=inputs_dict,
        operation_id="core.rendering.render_output",
        seed=seed
    )

    return {
        "rendered_text": rendered_text,
        "provenance": envelope["provenance"],
        "not_computable": None
    }


def load_fn_exports_deterministic(
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """Deterministic wrapper for core.fn_exports.load capability."""
    payload = {
        "owner": "Abraxas",
        "generated_at_unix": NOW,
        "functions": EXPORTS,
    }
    config = {
        "seed": seed,
        **kwargs
    }
    envelope = canonical_envelope(
        result=payload,
        config=config,
        inputs={},
        operation_id="core.fn_exports.load",
        seed=seed
    )
    return {
        "payload": payload,
        "provenance": envelope["provenance"],
        "not_computable": None
    }
