"""Schema for deterministic visual control frames."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class VisualControlFrame(BaseModel):
    window_utc: str = Field(..., description="Window identifier start/end")
    hue_range: List[float] = Field(..., description="Hue range [0..360]")
    saturation_level: float = Field(..., description="Saturation level [0..1]")
    luminance_level: float = Field(..., description="Luminance level [0..1]")
    motion_vector_strength: float = Field(..., description="Motion strength [0..1]")
    distortion_intensity: float = Field(..., description="Distortion intensity [0..1]")
    layering_depth: float = Field(..., description="Layering depth [0..1]")
    noise_floor: float = Field(..., description="Noise floor [0..1]")
    stillness_probability: float = Field(..., description="Stillness probability [0..1]")
    provenance: Dict[str, Any] = Field(default_factory=dict)
