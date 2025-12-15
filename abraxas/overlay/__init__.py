"""Abraxas Overlay Module

Provides overlay adaptation and phase management capabilities.
"""

from .adapter import OverlayAdapter
from .phases import PhaseManager
from .schema import OverlaySchema

__all__ = ["OverlayAdapter", "PhaseManager", "OverlaySchema"]
