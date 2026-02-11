# abraxas::mda::types::v0.1.0
# deterministic patch — resume verification cycle
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


def stable_json_dumps(obj: Any) -> str:
    """
    Deterministic JSON serialization.
    """
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sorted_unique_strs(items: Sequence[Any]) -> Tuple[str, ...]:
    """Return sorted unique non-None strings from a sequence."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item is not None and isinstance(item, str) and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(sorted(out))


@dataclass(frozen=True)
class ScoreVector:
    impact: float = 0.0
    velocity: float = 0.0
    uncertainty: float = 1.0
    polarity: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "impact": self.impact,
            "velocity": self.velocity,
            "uncertainty": self.uncertainty,
            "polarity": self.polarity,
        }


@dataclass(frozen=True)
class DomainSignalPack:
    domain: str
    subdomain: str
    status: str = "not_computable"
    scores: ScoreVector = field(default_factory=ScoreVector)
    events: Tuple[Any, ...] = ()
    evidence_refs: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "subdomain": self.subdomain,
            "status": self.status,
            "scores": self.scores.to_dict(),
            "events": list(self.events),
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class FusionEdge:
    src_id: str
    dst_id: str
    edge_type: str = "adjacent_dsp"
    weight: float = 1.0


@dataclass(frozen=True)
class FusionGraph:
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: Tuple[FusionEdge, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": dict(self.nodes),
            "edges": [
                {"src_id": e.src_id, "dst_id": e.dst_id, "edge_type": e.edge_type, "weight": e.weight}
                for e in self.edges
            ],
        }


@dataclass
class MDARunEnvelope:
    env: str = "sandbox"
    seed: int = 0
    run_at: str = ""
    fixture_path: Optional[str] = None
    # Bridge/inputs mode fields
    run_at_iso: Optional[str] = None
    promotion_enabled: bool = False
    enabled_domains: Tuple[str, ...] = ()
    enabled_subdomains: Tuple[str, ...] = ()
    inputs: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        # Normalize: if run_at_iso provided but run_at empty, use run_at_iso
        if self.run_at_iso and not self.run_at:
            self.run_at = self.run_at_iso

    def input_hash(self) -> str:
        """Deterministic hash of inputs for provenance."""
        if self.inputs is not None:
            return sha256_hex(stable_json_dumps(self.inputs))
        if self.fixture_path is not None:
            return sha256_hex(self.fixture_path)
        return sha256_hex("")
