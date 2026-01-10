"""Deterministic atlas-to-audio control mappings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from abraxas.sonification.schema import AudioControlFrame


@dataclass(frozen=True)
class SonificationConstants:
    mapping_version: str = "sonify.v1.0"
    tempo_min_bpm: float = 40.0
    tempo_max_bpm: float = 160.0
    modulation_strength_scale: float = 0.5
    rhythm_density_scale: float = 0.4
    harmonic_rarity_weight: float = 1.0
    silence_stability_scale: float = 0.05
    spectral_variance_max: float = 0.25


SONIFICATION_CONSTANTS = SonificationConstants()


def build_audio_frames(
    atlas_pack: Dict[str, Any],
    *,
    constants: SonificationConstants = SONIFICATION_CONSTANTS,
) -> List[AudioControlFrame]:
    pressure_cells = atlas_pack.get("pressure_cells") or []
    if not pressure_cells:
        return []

    windows = _group_pressure_by_window(pressure_cells)
    jetstreams = atlas_pack.get("jetstreams") or []
    cyclones = atlas_pack.get("cyclones") or []
    calm_zones = atlas_pack.get("calm_zones") or []
    clusters = atlas_pack.get("synchronicity_clusters") or []

    rhythm_base = _rhythm_density_from_clusters(clusters, constants)

    frames: List[AudioControlFrame] = []
    for window_utc in sorted(windows.keys()):
        window_vectors = windows[window_utc]
        pressure_avg = _mean([val for val in window_vectors.values() if val is not None])
        tempo_bpm = _map_range(pressure_avg or 0.0, 0.0, 1.0, constants.tempo_min_bpm, constants.tempo_max_bpm)
        spectral_centroid = _spectral_centroid(window_vectors, constants)
        modulation_rate = _modulation_from_jetstreams(jetstreams, window_utc, constants)
        harmonic_tension = _harmonic_tension_from_cyclones(cyclones, window_utc, constants)
        silence_probability = _silence_from_calm_zones(calm_zones, window_utc, constants)

        frame = AudioControlFrame(
            window_utc=window_utc,
            tempo_bpm=_clamp(tempo_bpm, constants.tempo_min_bpm, constants.tempo_max_bpm),
            rhythm_density=_clamp(rhythm_base, 0.0, 1.0),
            spectral_centroid=_clamp(spectral_centroid, 0.0, 1.0),
            harmonic_tension=_clamp(harmonic_tension, 0.0, 1.0),
            modulation_rate=_clamp(modulation_rate, 0.0, 1.0),
            silence_probability=_clamp(silence_probability, 0.0, 1.0),
            provenance={
                "atlas_hash": atlas_pack.get("provenance", {}).get("atlas_hash"),
                "primitives_used": {
                    "pressure_cells": len(pressure_cells),
                    "jetstreams": len(jetstreams),
                    "cyclones": len(cyclones),
                    "calm_zones": len(calm_zones),
                    "synchronicity_clusters": len(clusters),
                },
                "mapping_version": constants.mapping_version,
            },
        )
        frames.append(frame)
    return frames


def _group_pressure_by_window(pressure_cells: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Optional[float]]]:
    windows: Dict[str, Dict[str, Optional[float]]] = {}
    for cell in pressure_cells:
        window = str(cell.get("window_utc") or "")
        vector = str(cell.get("vector") or "")
        intensity = cell.get("intensity")
        windows.setdefault(window, {})
        windows[window][vector] = float(intensity) if intensity is not None else None
    return windows


def _modulation_from_jetstreams(
    jetstreams: Iterable[Dict[str, Any]],
    window_utc: str,
    constants: SonificationConstants,
) -> float:
    total = 0.0
    for jet in jetstreams:
        directionality = jet.get("directionality") or []
        if window_utc not in directionality:
            continue
        strength = jet.get("strength") or 0.0
        total += float(strength) * constants.modulation_strength_scale
    return total


def _harmonic_tension_from_cyclones(
    cyclones: Iterable[Dict[str, Any]],
    window_utc: str,
    constants: SonificationConstants,
) -> float:
    total = 0.0
    for cyclone in cyclones:
        if str(cyclone.get("window_utc") or "") != window_utc:
            continue
        coherence = cyclone.get("coherence_score") or 0.0
        rarity = cyclone.get("rarity_score") or 0.0
        total += float(coherence) * float(rarity) * constants.harmonic_rarity_weight
    return total


def _silence_from_calm_zones(
    calm_zones: Iterable[Dict[str, Any]],
    window_utc: str,
    constants: SonificationConstants,
) -> float:
    total = 0.0
    for zone in calm_zones:
        duration = zone.get("duration_windows") or []
        if window_utc not in duration:
            continue
        stability = zone.get("stability_score") or 0.0
        total += float(stability) * constants.silence_stability_scale
    return total


def _rhythm_density_from_clusters(
    clusters: Iterable[Dict[str, Any]],
    constants: SonificationConstants,
) -> float:
    total = 0.0
    for cluster in clusters:
        density = cluster.get("density_score")
        if density is None:
            continue
        total += float(density) * constants.rhythm_density_scale
    return total


def _spectral_centroid(
    vectors: Dict[str, Optional[float]],
    constants: SonificationConstants,
) -> float:
    values = [val for val in vectors.values() if val is not None]
    if not values:
        return 0.0
    variance = _variance(values)
    return _map_range(variance, 0.0, constants.spectral_variance_max, 0.0, 1.0)


def _mean(values: Iterable[float]) -> Optional[float]:
    values = [float(val) for val in values if val is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _variance(values: List[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((val - mean) ** 2 for val in values) / len(values)


def _map_range(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    if in_max == in_min:
        return out_min
    ratio = (value - in_min) / (in_max - in_min)
    return out_min + ratio * (out_max - out_min)


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))
