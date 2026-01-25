from __future__ import annotations

from typing import Iterable, List

from ..types import DomainDescriptor, EvidenceRow, Motif


def _digit_runs(text: str) -> List[str]:
    runs: List[str] = []
    buf: List[str] = []
    for ch in text:
        if ch.isdigit():
            buf.append(ch)
            continue
        if ch in {"-", ":"}:
            continue
        if buf:
            runs.append("".join(buf))
            buf = []
    if buf:
        runs.append("".join(buf))
    return runs


def _ngrams(run: str, max_len: int = 6) -> Iterable[str]:
    length = len(run)
    for n in range(1, min(max_len, length) + 1):
        for i in range(0, length - n + 1):
            yield run[i:i + n]


def _motif_complexity(motif_len: int) -> float:
    return min(2.0, 1.0 + (motif_len / 10.0))


class DigitMotifCartridge:
    domain_id = "sdct.digit_motif.v1"

    def __init__(self) -> None:
        self._motif_kind = "digit"

    def descriptor(self) -> DomainDescriptor:
        return DomainDescriptor(
            domain_id=self.domain_id,
            domain_name="Digit Motifs",
            domain_version="1.0.0",
            motif_kind=self._motif_kind,
            alphabet="0-9",
            constraints=["digit_only", "max_ngram<=6"],
            params_schema_id="sdct.domain_params.v0",
        )

    def encode(self, item: dict) -> List[str]:
        blob = f"{item.get('title', '')}\n{item.get('text', '')}"
        return _digit_runs(blob)

    def extract_motifs(self, sym: List[str]) -> List[Motif]:
        motifs: List[Motif] = []
        seen = set()
        for run in sym:
            for gram in _ngrams(run, max_len=6):
                if gram in seen:
                    continue
                seen.add(gram)
                motif_id = f"{self._motif_kind}:{gram}"
                motifs.append(Motif(
                    domain_id=self.domain_id,
                    motif_id=motif_id,
                    motif_text=gram,
                    motif_len=len(gram),
                    motif_complexity=_motif_complexity(len(gram)),
                    lane_hint="canary",
                ))
        return sorted(motifs, key=lambda m: (m.motif_id, m.motif_text))

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
