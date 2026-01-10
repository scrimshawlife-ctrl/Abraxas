"""Rune adapter for ALIVE capabilities.

Thin adapter layer exposing abraxas.alive.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.alive.core import alive_run as alive_run_core
from abraxas.alive.models import ALIVERunInput, ALIVEFieldSignature


def alive_run_deterministic(
    artifact: Dict[str, Any],
    tier: str = "psychonaut",
    profile: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible ALIVE analysis runner.

    Executes ALIVE field signature analysis on artifact (text/media).

    Args:
        artifact: Normalized artifact bundle (text/url/meta)
        tier: Analysis tier ('psychonaut' | 'academic' | 'enterprise')
        profile: Onboarding weights/traits (optional)
        seed: Deterministic seed (for provenance)

    Returns:
        Dict with result, provenance, not_computable
    """
    # Run ALIVE core
    result = alive_run_core(artifact=artifact, tier=tier, profile=profile)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result=result,
        config={"tier": tier},
        inputs={"artifact": artifact, "profile": profile},
        operation_id="alive.run",
        seed=seed
    )

    return {
        "result": result,
        "provenance": envelope["provenance"],
        "not_computable": None
    }


def alive_parse_field_signature_deterministic(
    field_signature: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible ALIVE field signature parser.

    Validates and parses field signature using ALIVEFieldSignature model.

    Args:
        field_signature: Raw field signature dict
        seed: Deterministic seed (for provenance)

    Returns:
        Dict with parsed_signature, provenance, not_computable
    """
    # Parse using Pydantic model
    try:
        signature = ALIVEFieldSignature(**field_signature)
        parsed = signature.model_dump()
        parse_error = None
    except Exception as e:
        parsed = None
        parse_error = str(e)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"parsed_signature": parsed, "parse_error": parse_error},
        config={},
        inputs={"field_signature": field_signature},
        operation_id="alive.parse_field_signature",
        seed=seed
    )

    return {
        "parsed_signature": parsed,
        "parse_error": parse_error,
        "provenance": envelope["provenance"],
        "not_computable": None
    }


def alive_parse_run_input_deterministic(
    run_input: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible ALIVE run input parser.

    Validates and parses run input using ALIVERunInput model.

    Args:
        run_input: Raw run input dict
        seed: Deterministic seed (for provenance)

    Returns:
        Dict with parsed_input, provenance, not_computable
    """
    # Parse using Pydantic model
    try:
        input_model = ALIVERunInput(**run_input)
        parsed = input_model.model_dump()
        parse_error = None
    except Exception as e:
        parsed = None
        parse_error = str(e)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"parsed_input": parsed, "parse_error": parse_error},
        config={},
        inputs={"run_input": run_input},
        operation_id="alive.parse_run_input",
        seed=seed
    )

    return {
        "parsed_input": parsed,
        "parse_error": parse_error,
        "provenance": envelope["provenance"],
        "not_computable": None
    }


__all__ = [
    "alive_run_deterministic",
    "alive_parse_field_signature_deterministic",
    "alive_parse_run_input_deterministic",
]
