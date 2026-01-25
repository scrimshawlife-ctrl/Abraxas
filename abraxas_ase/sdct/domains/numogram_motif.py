from __future__ import annotations

from typing import Iterable, List

from ..numogram.spec_v1 import NumogramGraph
from ..numogram.walk import walk as numogram_walk
from ..types import DomainDescriptor, EvidenceRow, Motif


def _node_ngrams(nodes: List[str], min_len: int = 3, max_len: int = 6) -> Iterable[tuple[int, str]]:
    length = len(nodes)
    for n in range(min_len, min(max_len, length) + 1):
        for i in range(0, length - n + 1):
            yield n, "-".join(nodes[i:i + n])


def _edge_ngrams(nodes: List[str], min_len: int = 2, max_len: int = 5) -> Iterable[tuple[int, str]]:
    edges = [f"{nodes[i]}>{nodes[i + 1]}" for i in range(len(nodes) - 1)]
    length = len(edges)
    for n in range(min_len, min(max_len, length) + 1):
        for i in range(0, length - n + 1):
            yield n, ",".join(edges[i:i + n])


def _motif_complexity(motif_len: int) -> float:
    return min(2.0, 1.0 + (motif_len / 5.0))


class NumogramMotifCartridge:
    domain_id = "sdct.numogram_motif.v1"

    def __init__(self, *, graph: NumogramGraph, max_motifs: int = 120, steps: int = 24) -> None:
        self._graph = graph
        self._max_motifs = max_motifs
        self._steps = steps

    def descriptor(self) -> DomainDescriptor:
        return DomainDescriptor(
            domain_id=self.domain_id,
            domain_name="Numogram Motifs",
            domain_version="1.0.0",
            motif_kind="numogram",
            alphabet="a-g",
            constraints=["node_ngram:3-6", "edge_ngram:2-5", "max_motifs<=120"],
            params_schema_id="sdct.domain_params.v0",
        )

    def encode(self, event_key: str, date: str, signature: str) -> List[str]:
        return numogram_walk(self._graph, event_key, date, signature, steps=self._steps)

    def extract_motifs(self, sym: List[str]) -> List[Motif]:
        motifs: List[Motif] = []
        seen = set()
        for n, text in _node_ngrams(sym, min_len=3, max_len=6):
            motif_id = f"numo.node:{text}"
            if motif_id in seen:
                continue
            seen.add(motif_id)
            motifs.append(Motif(
                domain_id=self.domain_id,
                motif_id=motif_id,
                motif_text=text,
                motif_len=n,
                motif_complexity=_motif_complexity(n),
                lane_hint="canary",
            ))
        for n, text in _edge_ngrams(sym, min_len=2, max_len=5):
            motif_id = f"numo.edge:{text}"
            if motif_id in seen:
                continue
            seen.add(motif_id)
            motifs.append(Motif(
                domain_id=self.domain_id,
                motif_id=motif_id,
                motif_text=text,
                motif_len=n,
                motif_complexity=_motif_complexity(n),
                lane_hint="canary",
            ))
        motifs = sorted(motifs, key=lambda m: (m.motif_id, m.motif_text))
        return motifs[: self._max_motifs]

    def emit_evidence(
        self,
        item: dict,
        motifs: List[Motif],
        event_key: str,
    ) -> List[EvidenceRow]:
        item_id = str(item.get("id", ""))
        source = str(item.get("source", ""))
        evidence: List[EvidenceRow] = []
        for motif in motifs:
            evidence.append(EvidenceRow(
                domain_id=motif.domain_id,
                motif_id=motif.motif_id,
                item_id=item_id,
                source=source,
                event_key=event_key,
                mentions=1,
                signals={"tap": 0.0, "sas": 0.0, "pfdi": 0.0},
                tags={"lane": motif.lane_hint, "tier": 2},
                provenance={},
            ))
        return evidence
