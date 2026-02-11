"""
Rune adapter for core capabilities.

Provides deterministic capability wrappers for core Abraxas functions with SEED compliance.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope


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
    # Call core function (lazy import to avoid top-level coupling)
    from abraxas.core.rendering import render_output as render_output_core
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
    from abx.fn_exports import EXPORTS, NOW
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


def run_oracle_kernel_deterministic(
    user: Dict[str, Any],
    overlays: Dict[str, Any],
    day: str,
    checkin: Optional[str] = None,
    seed: Optional[int] = None,
    strict_execution: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Deterministic wrapper for core kernel oracle with provenance tracking.

    This capability provides access to the kernel-level oracle (abraxas.core.oracle_runner)
    through the ABX-Runes capability system.

    Args:
        user: User configuration dictionary (will be converted to UserConfig)
        overlays: Overlays configuration dictionary (will be converted to OverlaysConfig)
        day: Date string for the oracle run
        checkin: Optional checkin identifier
        seed: Optional seed for SEED compliance (unused by kernel oracle, for provenance)
        strict_execution: If True, raise on errors; if False, return not_computable
        **kwargs: Additional arguments (captured for provenance)

    Returns:
        Dict with keys:
            - readout (dict): The oracle readout
            - oracle_provenance (dict): Provenance from oracle execution
            - provenance (dict): SHA-256 capability envelope provenance
            - not_computable (dict|None): Error details if execution failed
    """
    # Lazy imports to avoid top-level coupling
    from abraxas.io.config import UserConfig, OverlaysConfig
    from abraxas.core.oracle_runner import run_oracle as run_oracle_kernel

    # Convert dicts to config objects
    user_config = (
        UserConfig.from_dict(user)
        if isinstance(user, dict)
        else UserConfig.default()
    )
    overlays_config = (
        OverlaysConfig.from_dict(overlays)
        if isinstance(overlays, dict)
        else OverlaysConfig.default()
    )

    inputs_dict = {
        "user": user,
        "overlays": overlays,
        "day": day,
        "checkin": checkin,
    }
    config_dict = {
        "seed": seed,
        **kwargs
    }

    try:
        oracle_outputs = run_oracle_kernel(user_config, overlays_config, day, checkin=checkin)
        readout = dict(oracle_outputs.readout)
        oracle_provenance = dict(oracle_outputs.provenance)

        envelope = canonical_envelope(
            result={"readout": readout, "oracle_provenance": oracle_provenance},
            config=config_dict,
            inputs=inputs_dict,
            operation_id="oracle.kernel.run",
            seed=seed
        )

        return {
            "readout": readout,
            "oracle_provenance": oracle_provenance,
            "provenance": envelope["provenance"],
            "not_computable": None
        }
    except Exception as e:
        if strict_execution:
            raise
        return {
            "readout": None,
            "oracle_provenance": None,
            "provenance": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            }
        }
