"""Abraxas Kernel Module

Core phase execution engine for the Abraxas overlay system.
"""

from .entry import run_phase, Phase

__all__ = ["run_phase", "Phase"]
