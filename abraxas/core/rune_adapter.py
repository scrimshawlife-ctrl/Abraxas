"""
Rune adapter for core capabilities.

Provides deterministic capability wrappers for core Abraxas functions with SEED compliance.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.core.rendering import render_output as render_output_core


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
        inputs=inputs_dict,
        outputs={"rendered_text": rendered_text},
        config=config_dict,
        errors=None
    )

    return {
        "rendered_text": rendered_text,
        "provenance": envelope["provenance"],
        "not_computable": None
    }
