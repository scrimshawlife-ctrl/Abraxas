from __future__ import annotations

from typing import Any, Dict, Optional


CANONICAL_DOMAINS = (
    "slang",
    "aalmanac",
    "culture",
    "finance",
    "geopolitics",
    "politics",
    "health",
    "tech",
    "other",
)


def infer_domain(envelope: Dict[str, Any]) -> str:
    """
    Best-effort domain mapping.

    Rules (deterministic, additive):
    - If envelope["domain"] is a known string, use it (lowercased).
    - Else if oracle v1 scores exist, infer from populated score blocks.
    - Else return "other".
    """
    d = envelope.get("domain")
    if isinstance(d, str) and d.strip():
        v = d.strip().lower()
        return v if v in CANONICAL_DOMAINS else "other"

    sig = envelope.get("oracle_signal")
    if isinstance(sig, dict):
        scores = sig.get("scores_v1")
        if isinstance(scores, dict):
            if isinstance(scores.get("slang"), dict):
                return "slang"
            if isinstance(scores.get("aalmanac"), dict):
                return "aalmanac"

    return "other"

