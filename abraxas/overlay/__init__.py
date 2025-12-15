"""Abraxas Overlay Module

Provides overlay adaptation and phase management capabilities.
"""

from .adapter import OverlayAdapter
from .phases import dispatch
from .schema import OverlaySchema, Phase

__all__ = ["OverlayAdapter", "dispatch", "OverlaySchema", "Phase"]
