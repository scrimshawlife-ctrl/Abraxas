"""Immutable delta atlas primitives for deterministic export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence


def _sorted_refs(refs: Iterable[str]) -> List[str]:
    return sorted({str(ref) for ref in refs if ref})


@dataclass(frozen=True)
class DeltaPressure:
    vector: str
    window_utc: str
    delta_intensity: Optional[float]
    delta_gradient: Optional[float]
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "vector": self.vector,
            "window_utc": self.window_utc,
            "delta_intensity": self.delta_intensity,
            "delta_gradient": self.delta_gradient,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }


@dataclass(frozen=True)
class DeltaJetstream:
    vectors_involved: Sequence[str]
    delta_strength: Optional[float]
    delta_persistence: Optional[float]
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "vectors_involved": list(self.vectors_involved),
            "delta_strength": self.delta_strength,
            "delta_persistence": self.delta_persistence,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }


@dataclass(frozen=True)
class DeltaCyclone:
    center_vectors: Sequence[str]
    delta_coherence: Optional[float]
    delta_rarity: Optional[float]
    appeared: bool
    disappeared: bool
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "center_vectors": list(self.center_vectors),
            "delta_coherence": self.delta_coherence,
            "delta_rarity": self.delta_rarity,
            "appeared": self.appeared,
            "disappeared": self.disappeared,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }


@dataclass(frozen=True)
class DeltaCalmZone:
    vectors: Sequence[str]
    delta_stability: Optional[float]
    duration_change: Optional[int]
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "vectors": list(self.vectors),
            "delta_stability": self.delta_stability,
            "duration_change": self.duration_change,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }


@dataclass(frozen=True)
class DeltaSynchronicityCluster:
    domains: Sequence[str]
    vectors: Sequence[str]
    delta_density: Optional[float]
    appeared: bool
    disappeared: bool
    provenance_refs: Sequence[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "domains": list(self.domains),
            "vectors": list(self.vectors),
            "delta_density": self.delta_density,
            "appeared": self.appeared,
            "disappeared": self.disappeared,
            "provenance_refs": _sorted_refs(self.provenance_refs),
        }
