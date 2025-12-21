# abraxas/pipelines/sco_pipeline.py
# Symbolic Compression Operator Pipeline

from __future__ import annotations
from typing import Dict, Iterable, List, Tuple
from collections import defaultdict

from abraxas.linguistic.transparency import TransparencyLexicon
from abraxas.operators.symbolic_compression import SymbolicCompressionOperator, SymbolicCompressionEvent

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
        freq: Dict[Tuple[str, str], int] = defaultdict(int)
        normalized_lexicon = self._normalize_lexicon(lexicon)
        text_by_id = {
            r.get("id", str(i)): (r["text"], r["text"].lower())
            for i, r in enumerate(records)
        }

        for _, (_, lower) in text_by_id.items():
            for canon, variants in normalized_lexicon:
                for variant, variant_lower in variants:
                    count = lower.count(variant_lower)
                    if count:
                        freq[(canon, variant_lower)] += count

        events: List[SymbolicCompressionEvent] = []

        # Score known pairs first
        for canon, variants in normalized_lexicon:
            for variant, variant_lower in variants:
                observed = freq[(canon, variant_lower)]
                if not observed:
                    continue
                for _, (text, lower) in text_by_id.items():
                    if variant_lower not in lower:
                        continue
                    for before, after in self._iter_contexts(text, lower, canon, variant_lower):
                        e = self.op.analyze(
                            original_token=canon,
                            replacement_token=variant_lower,
                            context_before=before,
                            context_after=after,
                            domain=domain,
                            observed_frequency=observed
                        )
                        if e:
                            events.append(e)

        return self._dedupe(events)

    def _normalize_lexicon(self, lexicon: List[Dict]) -> List[Tuple[str, List[Tuple[str, str]]]]:
        """Normalize lexicon entries to deterministic lower-cased tuples."""
        normalized: List[Tuple[str, List[Tuple[str, str]]]] = []
        for entry in lexicon:
            canonical = entry["canonical"].strip().lower()
            if not canonical:
                continue
            variants: List[Tuple[str, str]] = []
            seen = set()
            for raw in entry.get("variants", []):
                variant = raw.strip()
                if not variant:
                    continue
                variant_lower = variant.lower()
                if variant_lower in seen:
                    continue
                seen.add(variant_lower)
                variants.append((variant, variant_lower))
            normalized.append((canonical, variants))
        return normalized

    def _iter_contexts(self, text: str, lower: str, canon: str, variant_lower: str) -> Iterable[Tuple[str, str]]:
        """
        Yield deterministic before/after contexts for each occurrence of the variant.
        """
        start = lower.find(variant_lower)
        while start != -1:
            end = start + len(variant_lower)
            before = f"{text[:start]}{canon}{text[end:]}"
            yield before, text
            start = lower.find(variant_lower, end)

    def _dedupe(self, events: List[SymbolicCompressionEvent]) -> List[SymbolicCompressionEvent]:
        # Deduplicate by provenance hash (stable)
        seen = set()
        out: List[SymbolicCompressionEvent] = []
        for e in events:
            if e.provenance_sha256 not in seen:
                seen.add(e.provenance_sha256)
                out.append(e)
        return out
