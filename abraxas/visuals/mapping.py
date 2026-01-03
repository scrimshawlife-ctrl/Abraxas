"""Deterministic atlas-to-visual control mappings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from abraxas.visuals.schema import VisualControlFrame


@dataclass(frozen=True)
class VisualConstants:
    mapping_version: str = "visuals.v1.0"
    hue_center: float = 200.0
    hue_min: float = 0.0
    hue_max: float = 360.0
    hue_range_base: float = 30.0
    hue_range_max: float = 180.0
    saturation_min: float = 0.2
    saturation_max: float = 1.0
    luminance_min: float = 0.3
    luminance_max: float = 0.9
    motion_strength_scale: float = 0.5
    distortion_weight: float = 1.0
    layering_base: float = 0.2
    layering_scale: float = 0.1
    noise_variance_max: float = 0.25
    noise_floor_min: float = 0.0
    noise_floor_max: float = 1.0
    stillness_scale: float = 0.05


VISUAL_CONSTANTS = VisualConstants()


def build_visual_frames(
    atlas_pack: Dict[str, Any],
    *,
    constants: VisualConstants = VISUAL_CONSTANTS,
) -> List[VisualControlFrame]:
    pressure_cells = atlas_pack.get("pressure_cells") or []
    if not pressure_cells:
        return []

    windows = _group_pressure_by_window(pressure_cells)
    jetstreams = atlas_pack.get("jetstreams") or []
    cyclones = atlas_pack.get("cyclones") or []
    calm_zones = atlas_pack.get("calm_zones") or []
    clusters = atlas_pack.get("synchronicity_clusters") or []

    hue_range_width = _hue_range_from_clusters(clusters, constants)

    frames: List[VisualControlFrame] = []
    for window_utc in sorted(windows.keys()):
        window_vectors = windows[window_utc]
        avg_pressure = _mean([val for val in window_vectors.values() if val is not None]) or 0.0

        saturation_level = _map_range(avg_pressure, 0.0, 1.0, constants.saturation_min, constants.saturation_max)
        luminance_level = _map_range(avg_pressure, 0.0, 1.0, constants.luminance_max, constants.luminance_min)
        motion_vector_strength = _motion_from_jetstreams(jetstreams, window_utc, constants)
        distortion_intensity = _distortion_from_cyclones(cyclones, window_utc, constants)
        layering_depth = _layering_from_cyclones(cyclones, window_utc, constants)
        noise_floor = _noise_from_variance(window_vectors, constants)
        stillness_probability = _stillness_from_calm_zones(calm_zones, window_utc, constants)

        noise_floor = _clamp(noise_floor - stillness_probability, constants.noise_floor_min, constants.noise_floor_max)

        hue_min, hue_max = _centered_hue_range(constants.hue_center, hue_range_width, constants.hue_min, constants.hue_max)

        frame = VisualControlFrame(
            window_utc=window_utc,
            hue_range=[hue_min, hue_max],
            saturation_level=_clamp(saturation_level, constants.saturation_min, constants.saturation_max),
            luminance_level=_clamp(luminance_level, constants.luminance_min, constants.luminance_max),
            motion_vector_strength=_clamp(motion_vector_strength, 0.0, 1.0),
            distortion_intensity=_clamp(distortion_intensity, 0.0, 1.0),
            layering_depth=_clamp(layering_depth, 0.0, 1.0),
            noise_floor=_clamp(noise_floor, constants.noise_floor_min, constants.noise_floor_max),
            stillness_probability=_clamp(stillness_probability, 0.0, 1.0),
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


def _motion_from_jetstreams(
    jetstreams: Iterable[Dict[str, Any]],
    window_utc: str,
    constants: VisualConstants,
) -> float:
    total = 0.0
    for jet in jetstreams:
        directionality = jet.get("directionality") or []
        if window_utc not in directionality:
            continue
        strength = jet.get("strength") or 0.0
        total += float(strength) * constants.motion_strength_scale
    return total


def _distortion_from_cyclones(
    cyclones: Iterable[Dict[str, Any]],
    window_utc: str,
    constants: VisualConstants,
) -> float:
    total = 0.0
    for cyclone in cyclones:
        if str(cyclone.get("window_utc") or "") != window_utc:
            continue
        coherence = cyclone.get("coherence_score") or 0.0
        rarity = cyclone.get("rarity_score") or 0.0
        total += float(coherence) * float(rarity) * constants.distortion_weight
    return total


def _layering_from_cyclones(
    cyclones: Iterable[Dict[str, Any]],
    window_utc: str,
    constants: VisualConstants,
) -> float:
    total = constants.layering_base
    for cyclone in cyclones:
        if str(cyclone.get("window_utc") or "") != window_utc:
            continue
        vectors = cyclone.get("center_vectors") or []
        total += len(vectors) * constants.layering_scale
    return total


def _stillness_from_calm_zones(
    calm_zones: Iterable[Dict[str, Any]],
    window_utc: str,
    constants: VisualConstants,
) -> float:
    total = 0.0
    for zone in calm_zones:
        duration = zone.get("duration_windows") or []
        if window_utc not in duration:
            continue
        stability = zone.get("stability_score") or 0.0
        total += float(stability) * constants.stillness_scale
    return total


def _hue_range_from_clusters(
    clusters: Iterable[Dict[str, Any]],
    constants: VisualConstants,
) -> float:
    density = 0.0
    for cluster in clusters:
        score = cluster.get("density_score")
        if score is None:
            continue
        density += float(score)
    return _clamp(constants.hue_range_base + density, constants.hue_range_base, constants.hue_range_max)


def _noise_from_variance(
    vectors: Dict[str, Optional[float]],
    constants: VisualConstants,
) -> float:
    values = [val for val in vectors.values() if val is not None]
    if not values:
        return 0.0
    variance = _variance(values)
    return _map_range(variance, 0.0, constants.noise_variance_max, constants.noise_floor_min, constants.noise_floor_max)


def _centered_hue_range(center: float, width: float, min_value: float, max_value: float) -> tuple[float, float]:
    half = width / 2.0
    start = _clamp(center - half, min_value, max_value)
    end = _clamp(center + half, min_value, max_value)
    return start, end


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
