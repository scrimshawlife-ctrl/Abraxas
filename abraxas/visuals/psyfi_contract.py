"""PsyFi interface contract for VisualControlSequence."""

from __future__ import annotations

from typing import Dict

PSYFI_CONTRACT: Dict[str, str] = {
    "hue_range": "Hue range bounds [0..360].",
    "saturation_level": "Normalized saturation [0..1].",
    "luminance_level": "Normalized luminance [0..1].",
    "motion_vector_strength": "Normalized motion strength [0..1].",
    "distortion_intensity": "Normalized distortion [0..1].",
    "layering_depth": "Normalized layering depth [0..1].",
    "noise_floor": "Normalized noise floor [0..1].",
    "stillness_probability": "Normalized stillness probability [0..1].",
    "window_utc": "Window identifier start/end (UTC).",
    "provenance": "Mapping provenance with atlas_hash and mapping_version.",
}
