from __future__ import annotations

from typing import Any, Dict


def quality_gate(entry: Dict[str, Any]) -> bool:
    term_class = str(entry.get("term_class", ""))
    term_canonical = str(entry.get("term_canonical", ""))
    mutation_type = str(entry.get("mutation_type", ""))
    signals = entry.get("signals", {}) or {}
    plausibility = float(signals.get("plausibility", 0.0) or 0.0)
    stickiness = float(signals.get("stickiness", 0.0) or 0.0)

    if term_class == "single" and " " in term_canonical:
        return False
    if mutation_type == "neologism" and plausibility < 0.55:
        return False
    if mutation_type == "phonetic_flip" and stickiness < 0.6:
        return False
    return True


def rejection_reason(entry: Dict[str, Any]) -> str:
    term_class = str(entry.get("term_class", ""))
    term_canonical = str(entry.get("term_canonical", ""))
    mutation_type = str(entry.get("mutation_type", ""))
    signals = entry.get("signals", {}) or {}
    plausibility = float(signals.get("plausibility", 0.0) or 0.0)
    stickiness = float(signals.get("stickiness", 0.0) or 0.0)

    if term_class == "single" and " " in term_canonical:
        return "single_has_multiple_tokens"
    if mutation_type == "neologism" and plausibility < 0.55:
        return "neologism_low_plausibility"
    if mutation_type == "phonetic_flip" and stickiness < 0.6:
        return "phonetic_flip_low_stickiness"
    return "accepted"
