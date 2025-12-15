# abraxas/linguistic/transparency.py
# Symbolic Transparency Index (STI) calculation

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable
import json
import hashlib

def token_transparency_heuristic(token: str) -> float:
    """
    Deterministic heuristic STI (Symbolic Transparency Index).
    Range [0,1]. Higher = more transparent/legible.
    Heuristics: shorter, common-looking, alphanumeric familiarity.
    Replace later with learned STI from corpora if desired.
    """
    t = token.strip()
    if not t:
        return 0.0
    # Penalize weird punctuation
    punct_penalty = sum(1 for c in t if not c.isalnum() and c not in (" ", "-", "'"))
    length = len(t)
    word_count = max(1, len([w for w in t.split() if w]))
    avg_word_len = length / word_count

    # Simple scoring
    score = 0.0
    score += max(0.0, 1.0 - (avg_word_len / 12.0))  # shorter words more transparent
    score += 0.15 if all(ch.isalnum() or ch in " -'" for ch in t) else 0.0
    score -= min(0.25, punct_penalty * 0.05)

    # Clamp
    return max(0.0, min(1.0, round(score, 6)))

@dataclass(frozen=True)
class TransparencyLexicon:
    """
    Token -> STI store with provenance hash.
    """
    mapping: Dict[str, float]
    provenance_sha256: str

    @staticmethod
    def build(tokens: Iterable[str]) -> "TransparencyLexicon":
        m: Dict[str, float] = {}
        for t in tokens:
            key = t.strip().lower()
            if key and key not in m:
                m[key] = token_transparency_heuristic(key)
        prov = _hash_mapping(m)
        return TransparencyLexicon(mapping=m, provenance_sha256=prov)

    @staticmethod
    def load_json(path: str) -> "TransparencyLexicon":
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return TransparencyLexicon(mapping=obj["mapping"], provenance_sha256=obj["provenance_sha256"])

    def save_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"mapping": self.mapping, "provenance_sha256": self.provenance_sha256}, f, indent=2, sort_keys=True)

    def sti(self, token: str) -> float:
        return self.mapping.get(token.strip().lower(), token_transparency_heuristic(token))

def _hash_mapping(m: Dict[str, float]) -> str:
    """Stable canonical JSON -> sha256"""
    s = json.dumps(m, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(s).hexdigest()
