"""Deterministic atlas construction from seedpacks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from abraxas.atlas.primitives import (
    CalmZone,
    Cyclone,
    Jetstream,
    PressureCell,
    SynchronicityCluster,
)
from abraxas.atlas.schema import ATLAS_SCHEMA_VERSION, AtlasPack
from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.tvm import TVM_VECTOR_IDS, _round_floats


@dataclass(frozen=True)
class AtlasConstants:
    min_jetstream_windows: int = 3
    cyclone_min_vectors: int = 3
    cyclone_cdec_threshold: float = 1.0
    calm_variance_threshold: float = 0.0005
    calm_min_windows: int = 3


ATLAS_CONSTANTS = AtlasConstants()


def load_seedpack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_atlas_pack(
    seedpack: Dict[str, Any],
    *,
    window_granularity: str,
    atlas_version: str = ATLAS_SCHEMA_VERSION,
) -> AtlasPack:
    frames = seedpack.get("frames") or []
    influence = seedpack.get("influence") or {}
    synchronicity = seedpack.get("synchronicity") or {}
    windows = _aggregate_windows(frames)

    pressure_cells = _build_pressure_cells(windows)
    jetstreams = _build_jetstreams(windows)
    cyclones = _build_cyclones(windows, influence, synchronicity)
    calm_zones = _build_calm_zones(windows)
    synchronicity_clusters = _build_synchronicity_clusters(synchronicity)

    seedpack_hash = seedpack.get("seedpack_hash") or sha256_hex(canonical_json(seedpack))
    provenance = {
        "seedpack_hash": seedpack_hash,
        "run_id": str(seedpack.get("provenance", {}).get("run_id") or seedpack.get("run_id") or "atlas_run"),
        "atlas_hash": "",
    }

    pack = AtlasPack(
        atlas_version=atlas_version,
        year=int(seedpack.get("year") or 0),
        window_granularity=window_granularity,
        frames_count=len(frames),
        pressure_cells=pressure_cells,
        jetstreams=jetstreams,
        cyclones=cyclones,
        calm_zones=calm_zones,
        synchronicity_clusters=synchronicity_clusters,
        provenance=provenance,
    )
    atlas_hash = pack.atlas_hash()
    pack.provenance["atlas_hash"] = atlas_hash
    return pack


def _aggregate_windows(frames: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for frame in frames:
        start = str(frame.get("window_start_utc") or "")
        end = str(frame.get("window_end_utc") or "")
        key = (start, end)
        grouped.setdefault(key, {"window_start_utc": start, "window_end_utc": end, "vectors": {}, "provenance_refs": []})
        vector_values = grouped[key]["vectors"]
        for vid in TVM_VECTOR_IDS:
            val = _extract_vector_score(frame.get("vectors") or {}, vid.value)
            if val is None:
                continue
            vector_values.setdefault(vid.value, []).append(float(val))
        grouped[key]["provenance_refs"].extend(_extract_provenance_refs(frame))

    windows: List[Dict[str, Any]] = []
    for key in sorted(grouped.keys()):
        entry = grouped[key]
        aggregated_vectors = {}
        for vid in TVM_VECTOR_IDS:
            values = entry["vectors"].get(vid.value) or []
            aggregated_vectors[vid.value] = _mean(values)
        windows.append(
            {
                "window_start_utc": entry["window_start_utc"],
                "window_end_utc": entry["window_end_utc"],
                "vectors": _round_floats(aggregated_vectors),
                "provenance_refs": sorted(set(entry["provenance_refs"])),
            }
        )
    return windows


def _extract_vector_score(vectors: Dict[str, Any], vector_id: str) -> Optional[float]:
    raw = vectors.get(vector_id)
    if isinstance(raw, dict):
        raw = raw.get("score")
    if raw is None:
        return None
    return float(raw)


def _extract_provenance_refs(frame: Dict[str, Any]) -> List[str]:
    provenance = frame.get("provenance") or {}
    refs = []
    for key in ("frame_hash", "inputs_hash"):
        value = provenance.get(key)
        if value:
            refs.append(str(value))
    return refs


def _build_pressure_cells(windows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pressure_cells: List[PressureCell] = []
    previous_values: Dict[str, Optional[float]] = {}
    for window in windows:
        window_id = _window_id(window)
        vectors = window.get("vectors") or {}
        for vid in TVM_VECTOR_IDS:
            value = vectors.get(vid.value)
            prev = previous_values.get(vid.value)
            gradient = None
            if value is not None and prev is not None:
                gradient = float(value) - float(prev)
            cell_id = f"{vid.value}:{window_id}"
            pressure_cells.append(
                PressureCell(
                    cell_id=cell_id,
                    vector=vid.value,
                    window_utc=window_id,
                    intensity=value,
                    gradient=gradient,
                    provenance_refs=window.get("provenance_refs") or [],
                )
            )
            previous_values[vid.value] = value
    return [cell.to_payload() for cell in pressure_cells]


def _build_jetstreams(windows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    jetstreams: List[Jetstream] = []
    window_ids = [_window_id(window) for window in windows]
    vectors_by_id = {vid.value: [] for vid in TVM_VECTOR_IDS}
    for window in windows:
        for vid in TVM_VECTOR_IDS:
            vectors_by_id[vid.value].append(window.get("vectors", {}).get(vid.value))

    for vector_id, values in vectors_by_id.items():
        sequence_start = 0
        direction = None
        for idx in range(1, len(values)):
            prev = values[idx - 1]
            cur = values[idx]
            if prev is None or cur is None:
                _finalize_jetstream(jetstreams, vector_id, values, window_ids, sequence_start, idx - 1, direction)
                sequence_start = idx
                direction = None
                continue
            current_direction = "up" if cur > prev else "down" if cur < prev else None
            if direction is None:
                direction = current_direction
                continue
            if current_direction != direction:
                _finalize_jetstream(jetstreams, vector_id, values, window_ids, sequence_start, idx - 1, direction)
                sequence_start = idx - 1
                direction = current_direction
        _finalize_jetstream(jetstreams, vector_id, values, window_ids, sequence_start, len(values) - 1, direction)

    return [jet.to_payload() for jet in sorted(jetstreams, key=lambda j: j.jet_id)]


def _finalize_jetstream(
    jetstreams: List[Jetstream],
    vector_id: str,
    values: Sequence[Optional[float]],
    window_ids: Sequence[str],
    start_idx: int,
    end_idx: int,
    direction: Optional[str],
) -> None:
    if end_idx - start_idx + 1 < ATLAS_CONSTANTS.min_jetstream_windows:
        return
    if direction is None:
        return
    slice_values = values[start_idx : end_idx + 1]
    deltas = []
    for a, b in zip(slice_values, slice_values[1:]):
        if a is None or b is None:
            continue
        deltas.append(abs(float(b) - float(a)))
    strength = _mean(deltas)
    directionality = list(window_ids[start_idx : end_idx + 1])
    jet_id = f"{vector_id}:{direction}:{directionality[0]}:{directionality[-1]}"
    jetstreams.append(
        Jetstream(
            jet_id=jet_id,
            vectors_involved=[vector_id],
            directionality=directionality,
            strength=strength,
            persistence=len(directionality),
            provenance_refs=[],
        )
    )


def _build_cyclones(
    windows: Sequence[Dict[str, Any]],
    influence: Dict[str, Any],
    synchronicity: Dict[str, Any],
) -> List[Dict[str, Any]]:
    cyclones: List[Cyclone] = []
    cdec_values = []
    for metric in (influence.get("ics") or {}).values():
        cdec = metric.get("CDEC")
        if cdec is not None:
            cdec_values.append(float(cdec))
    max_cdec = max(cdec_values) if cdec_values else 0.0

    coherence_score, rarity_score = _synchronicity_scores(synchronicity)
    provenance_refs = _synchronicity_refs(synchronicity) + _influence_refs(influence)

    previous_values: Dict[str, Optional[float]] = {}
    for window in windows:
        vectors = window.get("vectors") or {}
        gradients = {}
        for vid in TVM_VECTOR_IDS:
            value = vectors.get(vid.value)
            prev = previous_values.get(vid.value)
            if value is None or prev is None:
                continue
            gradients[vid.value] = float(value) - float(prev)
        previous_values = {vid.value: vectors.get(vid.value) for vid in TVM_VECTOR_IDS}

        positive_vectors = [vid for vid, delta in gradients.items() if delta > 0]
        if len(positive_vectors) < ATLAS_CONSTANTS.cyclone_min_vectors:
            continue
        if max_cdec < ATLAS_CONSTANTS.cyclone_cdec_threshold:
            continue
        center_vectors = sorted(positive_vectors, key=lambda vid: gradients.get(vid, 0.0), reverse=True)[:3]
        rotation_direction = "cw" if sum(gradients.values()) >= 0 else "ccw"
        window_id = _window_id(window)
        cyclone_id = f"{window_id}:{center_vectors[0] if center_vectors else 'none'}"
        cyclones.append(
            Cyclone(
                cyclone_id=cyclone_id,
                window_utc=window_id,
                center_vectors=center_vectors,
                domain_overlap=max_cdec,
                rotation_direction=rotation_direction,
                coherence_score=coherence_score,
                rarity_score=rarity_score,
                provenance_refs=provenance_refs + (window.get("provenance_refs") or []),
            )
        )

    return [cyclone.to_payload() for cyclone in cyclones]


def _build_calm_zones(windows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    calm_zones: List[CalmZone] = []
    window_ids = [_window_id(window) for window in windows]
    for vid in TVM_VECTOR_IDS:
        values = [window.get("vectors", {}).get(vid.value) for window in windows]
        streak_indices: List[int] = []
        streak_values: List[float] = []
        for idx, value in enumerate(values):
            if value is None:
                _finalize_calm_zone(calm_zones, vid.value, window_ids, streak_indices, _variance(streak_values))
                streak_indices = []
                streak_values = []
                continue
            next_values = streak_values + [float(value)]
            variance = _variance(next_values)
            if streak_values and variance >= ATLAS_CONSTANTS.calm_variance_threshold:
                _finalize_calm_zone(calm_zones, vid.value, window_ids, streak_indices, _variance(streak_values))
                streak_indices = [idx]
                streak_values = [float(value)]
                continue
            streak_indices.append(idx)
            streak_values = next_values
        _finalize_calm_zone(calm_zones, vid.value, window_ids, streak_indices, _variance(streak_values))
    return [zone.to_payload() for zone in calm_zones]


def _finalize_calm_zone(
    calm_zones: List[CalmZone],
    vector_id: str,
    window_ids: Sequence[str],
    streak: Sequence[int],
    last_variance: Optional[float],
) -> None:
    if len(streak) < ATLAS_CONSTANTS.calm_min_windows:
        return
    duration = [window_ids[idx] for idx in streak]
    stability = None
    if last_variance is not None:
        stability = 1.0 / max(last_variance, 1e-6)
    zone_id = f"{vector_id}:{duration[0]}:{duration[-1]}"
    calm_zones.append(
        CalmZone(
            zone_id=zone_id,
            vectors_suppressed=[vector_id],
            duration_windows=duration,
            stability_score=stability,
            provenance_refs=[],
        )
    )


def _build_synchronicity_clusters(synchronicity: Dict[str, Any]) -> List[Dict[str, Any]]:
    clusters: List[SynchronicityCluster] = []
    for envelope in synchronicity.get("envelopes") or []:
        domains = list(envelope.get("domains_involved") or [])
        vectors = list(envelope.get("vectors_activated") or [])
        time_window = str(envelope.get("time_window") or "")
        metrics = envelope.get("metrics") or {}
        density_score = _mean([metrics.get(key) for key in ("TCI", "SIS", "CPA", "RAC", "PUR") if metrics.get(key) is not None])
        provenance_refs = _synchronicity_refs(envelope)
        cluster_id = sha256_hex(canonical_json({"domains": domains, "vectors": vectors, "time_window": time_window}))
        clusters.append(
            SynchronicityCluster(
                cluster_id=cluster_id,
                domains=domains,
                vectors=vectors,
                time_window=time_window,
                density_score=density_score,
                provenance_refs=provenance_refs,
            )
        )
    return [cluster.to_payload() for cluster in sorted(clusters, key=lambda c: c.cluster_id)]


def _synchronicity_scores(synchronicity: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    sis_values = []
    rac_values = []
    rarity_values = []
    for envelope in synchronicity.get("envelopes") or []:
        metrics = envelope.get("metrics") or {}
        sis = metrics.get("SIS")
        rac = metrics.get("RAC")
        rarity = envelope.get("rarity_estimate")
        if sis is not None:
            sis_values.append(float(sis))
        if rac is not None:
            rac_values.append(float(rac))
        if rarity is not None:
            rarity_values.append(float(rarity))
    coherence_values = []
    if sis_values:
        coherence_values.append(_mean(sis_values))
    if rac_values:
        coherence_values.append(_mean(rac_values))
    coherence_score = _mean([val for val in coherence_values if val is not None]) if coherence_values else None
    rarity_score = _mean(rarity_values) if rarity_values else None
    return coherence_score, rarity_score


def _synchronicity_refs(synchronicity: Dict[str, Any]) -> List[str]:
    provenance = synchronicity.get("provenance") if isinstance(synchronicity, dict) else None
    refs = []
    if provenance and provenance.get("inputs_hash"):
        refs.append(str(provenance.get("inputs_hash")))
    if isinstance(synchronicity, dict):
        if synchronicity.get("provenance") is None and synchronicity.get("inputs_hash"):
            refs.append(str(synchronicity.get("inputs_hash")))
    return refs


def _influence_refs(influence: Dict[str, Any]) -> List[str]:
    provenance = influence.get("provenance") or {}
    refs = []
    if provenance.get("inputs_hash"):
        refs.append(str(provenance.get("inputs_hash")))
    return refs


def _window_id(window: Dict[str, Any]) -> str:
    return f"{window.get('window_start_utc')}/{window.get('window_end_utc')}"


def _mean(values: Iterable[float]) -> Optional[float]:
    values = [float(val) for val in values if val is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _variance(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((val - mean) ** 2 for val in values) / len(values)
