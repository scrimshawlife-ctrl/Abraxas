from __future__ import annotations

"""
Anagram Lexicon v0

Purpose:
  - Seed list of "high-signal" tokens for anagram target matching.
  - Deterministic, local, no network.

Rules:
  - Keep small and curated. This is a *bias surface*; treat as shadow-only.
  - Extend via config in evidence bundles later; do not auto-learn here.
"""

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class AnagramLexiconV0:
    # Single-word targets (normalized downstream)
    words: FrozenSet[str]
    # Multi-word targets written with spaces; downstream normalizer strips spaces for multiset matching
    phrases: FrozenSet[str]


DEFAULT_LEXICON_V0 = AnagramLexiconV0(
    words=frozenset({
        "oracle", "ritual", "analyst", "signal", "shadow", "drift", "canon", "ledger",
        "meme", "memes", "slang", "alias", "handle", "spoof", "noise", "entropy",
        "yggdrasil", "abraxas", "neon", "genie",
    }),
    phrases=frozenset({
        "signal layer",
        "memetic weather",
        "slang drift",
        "shadow metrics",
        "canon invariance",
    }),
)
