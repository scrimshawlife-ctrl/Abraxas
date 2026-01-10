from __future__ import annotations
from typing import Dict
from .base import AbraxasOverlay
from .neon_genie import NeonGenieOverlay
from .aalmanac import AALmanacOverlay
from .beatoven import BeatOvenOverlay


class OverlayRegistry:
    def __init__(self, overlays: Dict[str, AbraxasOverlay]):
        self._overlays = overlays

    def get(self, name: str) -> AbraxasOverlay:
        if name not in self._overlays:
            raise KeyError(f"Overlay not registered: {name}")
        return self._overlays[name]

    @classmethod
    def default(cls) -> "OverlayRegistry":
        overlays = {
            "neon_genie": NeonGenieOverlay(),
            "aalmanac": AALmanacOverlay(),
            "beatoven": BeatOvenOverlay(),
        }
        return cls(overlays)
