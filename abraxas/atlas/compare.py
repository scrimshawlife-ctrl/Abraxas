"""Deterministic delta atlas construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from abraxas.atlas.delta_primitives import (
    DeltaCalmZone,
    DeltaCyclone,
    DeltaJetstream,
    DeltaPressure,
    DeltaSynchronicityCluster,
)
from abraxas.atlas.delta_schema import DELTA_SCHEMA_VERSION, DeltaAtlasPack
from abraxas.core.canonical import canonical_json, sha256_hex


@dataclass(frozen=True)
class DeltaConstants:
    cyclone_overlap_threshold: float = 0.5


DELTA_CONSTANTS = DeltaConstants()


def build_delta_pack(
    base_atlas: Dict[str, Any],
    compare_atlas: Dict[str, Any],
    *,
    comparison_label: str,
    delta_version: str = DELTA_SCHEMA_VERSION,
    run_id: str = "delta_atlas",
) -> DeltaAtlasPack:
    _validate_alignment(base_atlas, compare_atlas)

    base_hash = base_atlas.get("provenance", {}).get("atlas_hash") or sha256_hex(canonical_json(base_atlas))
    compare_hash = compare_atlas.get("provenance", {}).get("atlas_hash") or sha256_hex(canonical_json(compare_atlas))

    delta_pressures = _build_delta_pressures(base_atlas, compare_atlas)
    delta_jetstreams = _build_delta_jetstreams(base_atlas, compare_atlas)
    delta_cyclones = _build_delta_cyclones(base_atlas, compare_atlas)
    delta_calm_zones = _build_delta_calm_zones(base_atlas, compare_atlas)
    delta_synchronicity = _build_delta_synchronicity(base_atlas, compare_atlas)

    frames_count = min(int(base_atlas.get("frames_count") or 0), int(compare_atlas.get("frames_count") or 0))
    pack = DeltaAtlasPack(
        delta_version=delta_version,
        base_atlas_hash=str(base_hash),
        compare_atlas_hash=str(compare_hash),
        comparison_label=comparison_label,
        window_granularity=str(base_atlas.get("window_granularity") or ""),
        frames_count=frames_count,
        delta_pressures=delta_pressures,
        delta_jetstreams=delta_jetstreams,
        delta_cyclones=delta_cyclones,
        delta_calm_zones=delta_calm_zones,
        delta_synchronicity_clusters=delta_synchronicity,
        provenance={"run_id": run_id, "delta_hash": ""},
    )
    pack.provenance["delta_hash"] = pack.delta_hash()
    return pack


def _validate_alignment(base_atlas: Dict[str, Any], compare_atlas: Dict[str, Any]) -> None:
    if base_atlas.get("window_granularity") != compare_atlas.get("window_granularity"):
        raise SystemExit("Atlas window granularity mismatch")
    base_windows = {cell.get("window_utc") for cell in base_atlas.get("pressure_cells") or []}
    compare_windows = {cell.get("window_utc") for cell in compare_atlas.get("pressure_cells") or []}
    if base_windows != compare_windows:
        raise SystemExit("Atlas window alignment mismatch")


def _build_delta_pressures(base_atlas: Dict[str, Any], compare_atlas: Dict[str, Any]) -> List[Dict[str, Any]]:
    base_cells = _index_pressure(base_atlas.get("pressure_cells") or [])
    compare_cells = _index_pressure(compare_atlas.get("pressure_cells") or [])
    keys = sorted(set(base_cells.keys()) | set(compare_cells.keys()))
    deltas: List[DeltaPressure] = []
    for vector, window in keys:
        base = base_cells.get((vector, window))
        comp = compare_cells.get((vector, window))
        delta_intensity = _delta_value(base, comp, "intensity")
        delta_gradient = _delta_value(base, comp, "gradient")
        refs = _merge_refs(base, comp)
        deltas.append(
            DeltaPressure(
                vector=vector,
                window_utc=window,
                delta_intensity=delta_intensity,
                delta_gradient=delta_gradient,
                provenance_refs=refs,
            )
        )
    return [delta.to_payload() for delta in deltas]


def _index_pressure(cells: Sequence[Dict[str, Any]]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    indexed: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for cell in cells:
        vector = str(cell.get("vector") or "")
        window = str(cell.get("window_utc") or "")
        indexed[(vector, window)] = cell
    return indexed


def _build_delta_jetstreams(base_atlas: Dict[str, Any], compare_atlas: Dict[str, Any]) -> List[Dict[str, Any]]:
    base = _index_jetstreams(base_atlas.get("jetstreams") or [])
    comp = _index_jetstreams(compare_atlas.get("jetstreams") or [])
    keys = sorted(set(base.keys()) | set(comp.keys()))
    deltas: List[DeltaJetstream] = []
    for key in keys:
        base_item = base.get(key)
        comp_item = comp.get(key)
        delta_strength = _delta_value(base_item, comp_item, "strength")
        delta_persistence = _delta_value(base_item, comp_item, "persistence")
        refs = _merge_refs(base_item, comp_item)
        deltas.append(
            DeltaJetstream(
                vectors_involved=list(key),
                delta_strength=delta_strength,
                delta_persistence=delta_persistence,
                provenance_refs=refs,
            )
        )
    return [delta.to_payload() for delta in deltas]


def _index_jetstreams(jetstreams: Sequence[Dict[str, Any]]) -> Dict[Tuple[str, ...], Dict[str, Any]]:
    indexed: Dict[Tuple[str, ...], Dict[str, Any]] = {}
    for jet in jetstreams:
        vectors = tuple(sorted(jet.get("vectors_involved") or []))
        indexed[vectors] = jet
    return indexed


def _build_delta_cyclones(base_atlas: Dict[str, Any], compare_atlas: Dict[str, Any]) -> List[Dict[str, Any]]:
    base = base_atlas.get("cyclones") or []
    compare = compare_atlas.get("cyclones") or []
    used_base: set[int] = set()
    deltas: List[DeltaCyclone] = []

    for comp in compare:
        comp_vectors = tuple(sorted(comp.get("center_vectors") or []))
        match_idx = _match_cyclone(comp_vectors, base, used_base)
        if match_idx is None:
            deltas.append(
                DeltaCyclone(
                    center_vectors=comp_vectors,
                    delta_coherence=None,
                    delta_rarity=None,
                    appeared=True,
                    disappeared=False,
                    provenance_refs=_merge_refs(None, comp),
                )
            )
            continue
        used_base.add(match_idx)
        base_item = base[match_idx]
        deltas.append(
            DeltaCyclone(
                center_vectors=comp_vectors,
                delta_coherence=_delta_value(base_item, comp, "coherence_score"),
                delta_rarity=_delta_value(base_item, comp, "rarity_score"),
                appeared=False,
                disappeared=False,
                provenance_refs=_merge_refs(base_item, comp),
            )
        )

    for idx, base_item in enumerate(base):
        if idx in used_base:
            continue
        base_vectors = tuple(sorted(base_item.get("center_vectors") or []))
        deltas.append(
            DeltaCyclone(
                center_vectors=base_vectors,
                delta_coherence=None,
                delta_rarity=None,
                appeared=False,
                disappeared=True,
                provenance_refs=_merge_refs(base_item, None),
            )
        )
    return [delta.to_payload() for delta in deltas]


def _match_cyclone(
    comp_vectors: Sequence[str],
    base_items: Sequence[Dict[str, Any]],
    used_base: set[int],
) -> Optional[int]:
    best_idx = None
    best_overlap = 0.0
    comp_set = set(comp_vectors)
    for idx, base_item in enumerate(base_items):
        if idx in used_base:
            continue
        base_vectors = set(base_item.get("center_vectors") or [])
        if not base_vectors or not comp_set:
            continue
        overlap = len(comp_set & base_vectors) / max(len(comp_set), 1)
        if overlap >= DELTA_CONSTANTS.cyclone_overlap_threshold and overlap > best_overlap:
            best_overlap = overlap
            best_idx = idx
    return best_idx


def _build_delta_calm_zones(base_atlas: Dict[str, Any], compare_atlas: Dict[str, Any]) -> List[Dict[str, Any]]:
    base = _index_calm_zones(base_atlas.get("calm_zones") or [])
    comp = _index_calm_zones(compare_atlas.get("calm_zones") or [])
    keys = sorted(set(base.keys()) | set(comp.keys()))
    deltas: List[DeltaCalmZone] = []
    for key in keys:
        base_item = base.get(key)
        comp_item = comp.get(key)
        delta_stability = _delta_value(base_item, comp_item, "stability_score")
        duration_change = _duration_change(base_item, comp_item)
        refs = _merge_refs(base_item, comp_item)
        deltas.append(
            DeltaCalmZone(
                vectors=list(key),
                delta_stability=delta_stability,
                duration_change=duration_change,
                provenance_refs=refs,
            )
        )
    return [delta.to_payload() for delta in deltas]


def _index_calm_zones(zones: Sequence[Dict[str, Any]]) -> Dict[Tuple[str, ...], Dict[str, Any]]:
    indexed: Dict[Tuple[str, ...], Dict[str, Any]] = {}
    for zone in zones:
        vectors = tuple(sorted(zone.get("vectors_suppressed") or zone.get("vectors") or []))
        indexed[vectors] = zone
    return indexed


def _build_delta_synchronicity(base_atlas: Dict[str, Any], compare_atlas: Dict[str, Any]) -> List[Dict[str, Any]]:
    base = _index_clusters(base_atlas.get("synchronicity_clusters") or [])
    comp = _index_clusters(compare_atlas.get("synchronicity_clusters") or [])
    keys = sorted(set(base.keys()) | set(comp.keys()))
    deltas: List[DeltaSynchronicityCluster] = []
    for key in keys:
        base_item = base.get(key)
        comp_item = comp.get(key)
        appeared = base_item is None and comp_item is not None
        disappeared = base_item is not None and comp_item is None
        delta_density = _delta_value(base_item, comp_item, "density_score")
        refs = _merge_refs(base_item, comp_item)
        deltas.append(
            DeltaSynchronicityCluster(
                domains=list(key[0]),
                vectors=list(key[1]),
                delta_density=delta_density,
                appeared=appeared,
                disappeared=disappeared,
                provenance_refs=refs,
            )
        )
    return [delta.to_payload() for delta in deltas]


def _index_clusters(clusters: Sequence[Dict[str, Any]]) -> Dict[Tuple[Tuple[str, ...], Tuple[str, ...]], Dict[str, Any]]:
    indexed: Dict[Tuple[Tuple[str, ...], Tuple[str, ...]], Dict[str, Any]] = {}
    for cluster in clusters:
        domains = tuple(sorted(cluster.get("domains") or []))
        vectors = tuple(sorted(cluster.get("vectors") or []))
        indexed[(domains, vectors)] = cluster
    return indexed


def _delta_value(base_item: Optional[Dict[str, Any]], comp_item: Optional[Dict[str, Any]], key: str) -> Optional[float]:
    if base_item is None or comp_item is None:
        return None
    base_val = base_item.get(key)
    comp_val = comp_item.get(key)
    if base_val is None or comp_val is None:
        return None
    return float(comp_val) - float(base_val)


def _duration_change(base_item: Optional[Dict[str, Any]], comp_item: Optional[Dict[str, Any]]) -> Optional[int]:
    if base_item is None or comp_item is None:
        return None
    base_duration = base_item.get("duration_windows") or []
    comp_duration = comp_item.get("duration_windows") or []
    return len(comp_duration) - len(base_duration)


def _merge_refs(base_item: Optional[Dict[str, Any]], comp_item: Optional[Dict[str, Any]]) -> List[str]:
    refs = []
    for item in (base_item, comp_item):
        if not item:
            continue
        refs.extend(item.get("provenance_refs") or [])
    return refs
