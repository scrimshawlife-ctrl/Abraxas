"""Schema for deterministic audio control frames."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class AudioControlFrame(BaseModel):
    window_utc: str = Field(..., description="Window identifier start/end")
    tempo_bpm: float = Field(..., description="Tempo in BPM")
    rhythm_density: float = Field(..., description="Rhythmic density [0..1]")
    spectral_centroid: float = Field(..., description="Spectral centroid [0..1]")
    harmonic_tension: float = Field(..., description="Harmonic tension [0..1]")
    modulation_rate: float = Field(..., description="Modulation rate [0..1]")
    silence_probability: float = Field(..., description="Silence probability [0..1]")
    provenance: Dict[str, Any] = Field(default_factory=dict)
