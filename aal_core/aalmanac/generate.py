from __future__ import annotations

from typing import Any, Dict, Iterable, List

from aal_core.aalmanac.mutation import detect_mutation
from aal_core.aalmanac.tokenizer import tokenize


def _metaphor_bind(handle: str, rune_bias: str) -> str:
    if not handle:
        return handle
    if rune_bias:
        return f"{handle}{rune_bias}"
    return handle


def propose_candidates(signal_packet: Dict[str, Any], *, lexicon: Iterable[str]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    memetic = signal_packet.get("memetic", {}) or {}
    handles = memetic.get("handles", []) or []
    dominant_domain = signal_packet.get("dominant_domain", "")
    symbolic_pressure = float(signal_packet.get("symbolic_pressure", 0.0) or 0.0)
    rune_bias = str(signal_packet.get("rune_bias", ""))

    for handle in handles:
        raw = str(handle)
        if not raw:
            continue
        mutation_type = detect_mutation(" ".join(tokenize(raw)), lexicon=lexicon)
        candidates.append({
            "term_raw": raw,
            "mutation_type": "context_shift" if mutation_type == "context_shift" else "neologism",
            "context": dominant_domain,
        })

        if symbolic_pressure > 0.6:
            bound = _metaphor_bind(raw, rune_bias)
            candidates.append({
                "term_raw": bound,
                "mutation_type": "metaphor_bind",
                "context": dominant_domain,
            })

    return candidates
