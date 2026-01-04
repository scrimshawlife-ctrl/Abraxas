"""
Shadow Output Normalizer.

Converts arbitrary detector outputs into a canonical dict shape:
- status: "ok" | "not_computable" | "error"
- value: payload (if ok)
- missing: list of missing inputs (if not_computable)
- error: string (if error)
- provenance: deterministic metadata

No censorship, no filtering — just typed structure.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional

from abraxas.detectors.shadow.types import ShadowResult, ShadowStatus


def normalize_shadow_output(
    *,
    name: str,
    out: Any,
    provenance: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Normalize arbitrary detector output into a canonical dict form.

    Deterministic, non-judgmental transformation.

    Accepted native forms:
    - ShadowResult dataclass
    - Dict with "status" key (respected as-is)
    - Anything else becomes {"status": "ok", "value": <out>}

    Args:
        name: Detector name (for provenance)
        out: Raw detector output
        provenance: Optional additional provenance metadata

    Returns:
        Dict with canonical shape: {status, value, missing, error, provenance}
    """
    provenance = provenance or {}
    # Build provenance with detector name first, then sorted additional keys
    prov = {"detector": name, **{k: provenance[k] for k in sorted(provenance.keys())}}

    # Case 1: ShadowResult dataclass
    if isinstance(out, ShadowResult):
        d = asdict(out)
        d["provenance"] = {**prov, **(d.get("provenance") or {})}
        return d

    # Case 2: Dict with status key (respect caller's intent)
    if isinstance(out, dict) and "status" in out:
        d = dict(out)
        d.setdefault("missing", [])
        d.setdefault("error", None)
        d.setdefault("value", None if d.get("status") != "ok" else d.get("value"))
        d["provenance"] = {**prov, **(d.get("provenance") or {})}
        return d

    # Case 3: Default — treat as ok payload
    return {
        "status": "ok",
        "value": out,
        "missing": [],
        "error": None,
        "provenance": prov,
    }


def wrap_shadow_task(
    name: str, fn: Callable[[Dict[str, Any]], Any]
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Wrap a shadow detector callable into a normalizing wrapper.

    The wrapped function:
    - Calls the original function with context
    - Normalizes output to canonical shape
    - Catches exceptions and returns structured error

    Args:
        name: Detector name (for provenance and error reporting)
        fn: Original callable(context) -> Any

    Returns:
        Wrapped callable(context) -> Dict[str, Any] with canonical shape
    """

    def _wrapped(ctx: Dict[str, Any]) -> Dict[str, Any]:
        try:
            out = fn(ctx)
            return normalize_shadow_output(
                name=name, out=out, provenance={"wrapper": "shadow.normalize.v0"}
            )
        except Exception as e:
            return normalize_shadow_output(
                name=name,
                out={
                    "status": "error",
                    "error": f"{type(e).__name__}: {e}",
                    "value": None,
                    "missing": [],
                },
                provenance={"wrapper": "shadow.normalize.v0"},
            )

    return _wrapped


# === Helper functions for detectors ===


def not_computable(missing: List[str], provenance: Optional[Dict[str, Any]] = None) -> ShadowResult:
    """
    Create a not_computable ShadowResult.

    Use this in detectors when required inputs are missing:

        if "text" not in ctx:
            return not_computable(["text"])

    Args:
        missing: List of missing input keys
        provenance: Optional provenance metadata

    Returns:
        ShadowResult with status="not_computable"
    """
    return ShadowResult(
        status="not_computable",
        value=None,
        missing=missing,
        error=None,
        provenance=provenance or {},
    )


def ok(value: Any, provenance: Optional[Dict[str, Any]] = None) -> ShadowResult:
    """
    Create an ok ShadowResult.

    Use this in detectors for successful computation:

        return ok({"score": 0.75, "confidence": 0.9})

    Args:
        value: Result payload
        provenance: Optional provenance metadata

    Returns:
        ShadowResult with status="ok"
    """
    return ShadowResult(
        status="ok",
        value=value,
        missing=[],
        error=None,
        provenance=provenance or {},
    )


def error(message: str, provenance: Optional[Dict[str, Any]] = None) -> ShadowResult:
    """
    Create an error ShadowResult.

    Use this in detectors when computation fails:

        return error("Division by zero in metric calculation")

    Args:
        message: Error message
        provenance: Optional provenance metadata

    Returns:
        ShadowResult with status="error"
    """
    return ShadowResult(
        status="error",
        value=None,
        missing=[],
        error=message,
        provenance=provenance or {},
    )


__all__ = [
    "normalize_shadow_output",
    "wrap_shadow_task",
    "not_computable",
    "ok",
    "error",
]
