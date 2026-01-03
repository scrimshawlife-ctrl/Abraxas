"""Immutable atlas primitives for deterministic export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence


def _sorted_refs(refs: Iterable[str]) -> List[str]:
    return sorted({str(ref) for ref in refs if ref})


@dataclass(frozen=True)
class PressureCell:
    cell_id: str
    vector: str
    window_utc: str
    intensity: Optional[float]
    gradient: Optional[float]
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "vector": self.vector,
            "window_utc": self.window_utc,
            "intensity": self.intensity,
            "gradient": self.gradient,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }


@dataclass(frozen=True)
class Jetstream:
    jet_id: str
    vectors_involved: Sequence[str]
    directionality: Sequence[str]
    strength: Optional[float]
    persistence: int
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "jet_id": self.jet_id,
            "vectors_involved": list(self.vectors_involved),
            "directionality": list(self.directionality),
            "strength": self.strength,
            "persistence": self.persistence,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }


@dataclass(frozen=True)
class Cyclone:
    cyclone_id: str
    window_utc: str
    center_vectors: Sequence[str]
    domain_overlap: float
    rotation_direction: str
    coherence_score: Optional[float]
    rarity_score: Optional[float]
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "cyclone_id": self.cyclone_id,
            "window_utc": self.window_utc,
            "center_vectors": list(self.center_vectors),
            "domain_overlap": self.domain_overlap,
            "rotation_direction": self.rotation_direction,
            "coherence_score": self.coherence_score,
            "rarity_score": self.rarity_score,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }


@dataclass(frozen=True)
class CalmZone:
    zone_id: str
    vectors_suppressed: Sequence[str]
    duration_windows: Sequence[str]
    stability_score: Optional[float]
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "vectors_suppressed": list(self.vectors_suppressed),
            "duration_windows": list(self.duration_windows),
            "stability_score": self.stability_score,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }


@dataclass(frozen=True)
class SynchronicityCluster:
    cluster_id: str
    domains: Sequence[str]
    vectors: Sequence[str]
    time_window: str
    density_score: Optional[float]
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "domains": list(self.domains),
            "vectors": list(self.vectors),
            "time_window": self.time_window,
            "density_score": self.density_score,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }
