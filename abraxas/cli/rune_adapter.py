"""Rune adapter for CLI capabilities.

Thin adapter layer exposing abraxas.cli.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.cli.counterfactual import run_counterfactual_cli as run_counterfactual_cli_core
from abraxas.cli.smv import run_smv_cli as run_smv_cli_core


def run_counterfactual_cli_deterministic(
    args: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible counterfactual CLI runner.

    Executes counterfactual replay engine with given arguments.

    Args:
        args: CLI arguments dict (run_id, portfolio, mask, cases_dir, etc.)
        seed: Deterministic seed (for provenance)

    Returns:
        Dict with exit_code, provenance, not_computable
    """
    # Create args namespace from dict
    import argparse
    ns = argparse.Namespace(**args)

    # Run CLI function (it prints to stdout and returns exit code)
    exit_code = run_counterfactual_cli_core(ns)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"exit_code": exit_code},
        config={},
        inputs={"args": args},
        operation_id="cli.counterfactual",
        seed=seed
    )

    return {
        "exit_code": exit_code,
        "provenance": envelope["provenance"],
        "not_computable": None
    }


def run_smv_cli_deterministic(
    args: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible SMV CLI runner.

    Executes signal marginal value analysis with given arguments.

    Args:
        args: CLI arguments dict (run_id, portfolio, vector_map, etc.)
        seed: Deterministic seed (for provenance)

    Returns:
        Dict with exit_code, provenance, not_computable
    """
    # Create args namespace from dict
    import argparse
    ns = argparse.Namespace(**args)

    # Run CLI function (it prints to stdout and returns exit code)
    exit_code = run_smv_cli_core(ns)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"exit_code": exit_code},
        config={},
        inputs={"args": args},
        operation_id="cli.smv",
        seed=seed
    )

    return {
        "exit_code": exit_code,
        "provenance": envelope["provenance"],
        "not_computable": None
    }


__all__ = [
    "run_counterfactual_cli_deterministic",
    "run_smv_cli_deterministic",
]
