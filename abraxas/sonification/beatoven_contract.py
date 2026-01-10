"""BeatOven interface contract for AudioControlSequence."""

from __future__ import annotations

from typing import Dict

BEATOVEN_CONTRACT: Dict[str, str] = {
    "tempo_bpm": "Tempo in BPM (bounded).",
    "rhythm_density": "Normalized rhythmic density [0..1].",
    "spectral_centroid": "Normalized spectral centroid [0..1].",
    "harmonic_tension": "Normalized harmonic tension [0..1].",
    "modulation_rate": "Normalized modulation rate [0..1].",
    "silence_probability": "Normalized probability of silence [0..1].",
    "window_utc": "Window identifier start/end (UTC).",
    "provenance": "Mapping provenance with atlas_hash and mapping_version.",
}
