"""Overlay phase dispatcher.

This module is intentionally thin: it forwards overlay phase requests to the
kernel router so phase behavior stays centralized and deterministic.
"""

from __future__ import annotations

from typing import Any, Dict

from abraxas.kernel.entry import run_phase

from .schema import Phase


def dispatch(phase: Phase, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a phase execution request to the kernel."""

    return run_phase(phase, payload)
