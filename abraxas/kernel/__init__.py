"""Abraxas Kernel Module

This module provides the core execution engine for Abraxas phases.
It includes whitelisted ASCEND operations and phase routing.
"""

from abraxas.kernel.entry import run_phase, Phase
from abraxas.kernel.ascend_ops import execute_ascend, OPS

__all__ = [
    "run_phase",
    "Phase",
    "execute_ascend",
    "OPS",
]
