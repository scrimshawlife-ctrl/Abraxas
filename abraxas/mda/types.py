from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import hashlib
import json


def stable_json_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MDARunEnvelope:
    env: str
    seed: int
    run_at: str
    fixture_path: str

    def input_hash(self) -> str:
        # The input hash is a contract: it must only depend on the run inputs.
        return sha256_hex(
            stable_json_dumps(
                {
                    "env": self.env,
                    "seed": self.seed,
                    "run_at": self.run_at,
                    "fixture_path": self.fixture_path,
                }
            )
        )


@dataclass(frozen=True)
class ScoreVector:
    impact: float
    velocity: float
    uncertainty: float
    polarity: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "impact": float(self.impact),
            "velocity": float(self.velocity),
            "uncertainty": float(self.uncertainty),
            "polarity": float(self.polarity),
        }


@dataclass(frozen=True)
class DomainSignalPack:
    domain: str
    subdomain: str
    status: str
    scores: ScoreVector
    events: Tuple[Dict[str, Any], ...]
    evidence_refs: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "subdomain": self.subdomain,
            "status": self.status,
            "scores": self.scores.to_dict(),
            "events": list(self.events),
            "evidence_refs": list(self.evidence_refs),
        }

    def stable_hash(self) -> str:
        return sha256_hex(stable_json_dumps(self.to_dict()))


@dataclass(frozen=True)
class FusionEdge:
    src_id: str
    dst_id: str
    edge_type: str
    evidence_refs: Tuple[str, ...] = ()
    weight: float = 1.0
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "src_id": self.src_id,
            "dst_id": self.dst_id,
            "edge_type": self.edge_type,
            "evidence_refs": list(self.evidence_refs),
            "weight": float(self.weight),
            "notes": self.notes,
        }

    def stable_hash(self) -> str:
        return sha256_hex(stable_json_dumps(self.to_dict()))


@dataclass(frozen=True)
class FusionGraph:
    nodes: Dict[str, Dict[str, Any]]
    edges: Tuple[FusionEdge, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": [e.to_dict() for e in self.edges],
        }

    def stable_hash(self) -> str:
        # Canonicalize edges deterministically (type, src, dst, then content).
        edges_sorted = sorted(
            self.edges, key=lambda e: (e.edge_type, e.src_id, e.dst_id, e.weight, e.notes or "")
        )
        obj = {
            "nodes": self.nodes,
            "edges": [e.to_dict() for e in edges_sorted],
        }
        return sha256_hex(stable_json_dumps(obj))


def sorted_unique_strs(items: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted({str(x) for x in items if str(x).strip()}))

