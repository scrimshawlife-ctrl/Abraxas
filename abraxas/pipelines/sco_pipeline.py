# abraxas/pipelines/sco_pipeline.py
# Symbolic Compression Operator Pipeline

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from collections import defaultdict

from abraxas.linguistic.transparency import TransparencyLexicon
from abraxas.operators.symbolic_compression import SymbolicCompressionOperator, SymbolicCompressionEvent

@dataclass(frozen=True)
class CandidatePair:
    original: str
    replacement: str
    domain: str

class SCOPipeline:
    """
    End-to-end pipeline:
    1) Find candidate replacement pairs (lightweight)
    2) Score with SCO/ECO operator
    3) Emit events
    """
    def __init__(self, transparency: TransparencyLexicon):
        self.op = SymbolicCompressionOperator(transparency)

    def run(
        self,
        records: List[Dict],
        lexicon: List[Dict],
        domain: str = "general"
    ) -> List[SymbolicCompressionEvent]:
        """
        records: [{"text": "...", "id": "..."}]
        lexicon: [{"canonical": "aphex twin", "variants": ["aphex twins", "apex twin", ...]}]
                 OR [{"canonical": "..."}] and pipeline will mine candidates automatically.
        """
        # Frequency estimate of replacements (how often we see replacement token)
        freq = defaultdict(int)
        text_by_id = {r.get("id", str(i)): r["text"] for i, r in enumerate(records)}

        for r in records:
            t = r["text"].lower()
            for entry in lexicon:
                canon = entry["canonical"].lower()
                # count occurrences of any known variants
                for v in entry.get("variants", []):
                    if v.lower() in t:
                        freq[(canon, v.lower())] += 1

        events: List[SymbolicCompressionEvent] = []

        # Score known pairs first
        for entry in lexicon:
            canon = entry["canonical"].lower()
            variants = [v.lower() for v in entry.get("variants", [])]
            for v in variants:
                # contexts: we build before/after using same text for determinism
                for rid, txt in text_by_id.items():
                    lower = txt.lower()
                    if v in lower:
                        before = lower.replace(v, canon)
                        after = lower
                        e = self.op.analyze(
                            original_token=canon,
                            replacement_token=v,
                            context_before=before,
                            context_after=after,
                            domain=domain,
                            observed_frequency=freq[(canon, v)]
                        )
                        if e:
                            events.append(e)

        return self._dedupe(events)

    def _dedupe(self, events: List[SymbolicCompressionEvent]) -> List[SymbolicCompressionEvent]:
        # Deduplicate by provenance hash (stable)
        seen = set()
        out: List[SymbolicCompressionEvent] = []
        for e in events:
            if e.provenance_sha256 not in seen:
                seen.add(e.provenance_sha256)
                out.append(e)
        return out
