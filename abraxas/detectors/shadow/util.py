"""
Shadow Detector Utilities — Ergonomic helpers for detector authors.

Standard helper functions to create canonical ShadowResult responses:
- ok(value, **prov) → successful computation
- not_computable(missing, **prov) → missing inputs
- err(message, **prov) → error state

These reduce boilerplate and ensure consistent structure across all detectors.

Usage in detectors:
    from abraxas.detectors.shadow.util import ok, not_computable, err

    def run_shadow(ctx):
        text = ctx.get("text")
        if text is None:
            return not_computable(["text"])

        if not text.strip():
            return err("Empty text provided")

        score = compute_score(text)
        return ok({"score": score}, provenance={"algo": "v1"})
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.detectors.shadow.types import ShadowResult


def ok(value: Any, provenance: Optional[Dict[str, Any]] = None) -> ShadowResult:
    """
    Create a successful ShadowResult.

    Args:
        value: Computation result payload
        provenance: Optional provenance metadata

    Returns:
        ShadowResult with status="ok"

    Example:
        return ok({"score": 0.75, "confidence": 0.9})
        return ok({"tokens": ["a", "b"]}, provenance={"version": "1.0"})
    """
    return ShadowResult(
        status="ok",
        value=value,
        missing=[],
        error=None,
        provenance=provenance or {},
    )


def not_computable(
    missing: List[str], provenance: Optional[Dict[str, Any]] = None
) -> ShadowResult:
    """
    Create a not_computable ShadowResult for missing inputs.

    Args:
        missing: List of missing input key names
        provenance: Optional provenance metadata

    Returns:
        ShadowResult with status="not_computable"

    Example:
        if "text" not in ctx:
            return not_computable(["text"])

        if "text" not in ctx or "tokens" not in ctx:
            return not_computable(["text", "tokens"])
    """
    return ShadowResult(
        status="not_computable",
        value=None,
        missing=list(missing),
        error=None,
        provenance=provenance or {},
    )


def err(message: str, provenance: Optional[Dict[str, Any]] = None) -> ShadowResult:
    """
    Create an error ShadowResult.

    Args:
        message: Error description
        provenance: Optional provenance metadata

    Returns:
        ShadowResult with status="error"

    Example:
        return err("Division by zero in score calculation")
        return err("Invalid input format", provenance={"stage": "parsing"})
    """
    return ShadowResult(
        status="error",
        value=None,
        missing=[],
        error=message,
        provenance=provenance or {},
    )


__all__ = ["ok", "not_computable", "err"]
