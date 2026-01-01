"""
Resonance Narratives renderer (v0.1, renderer-only).
"""

from .renderer import NarrativeError, RenderConfig, render
from .rules import NarrativeRules, default_rules

__all__ = [
    "NarrativeError",
    "NarrativeRules",
    "RenderConfig",
    "default_rules",
    "render",
]

