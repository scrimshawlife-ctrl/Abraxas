"""Deterministic linguistic normalization utilities."""

from __future__ import annotations

import re
from typing import List

TOKEN_RE = re.compile(r"[A-Za-z0-9']+")


def tokenize(text: str) -> List[str]:
    tokens = TOKEN_RE.findall(text.lower())
    return tokens


def stable_lang(text: str) -> str:
    ascii_ratio = sum(1 for ch in text if ord(ch) < 128) / max(len(text), 1)
    return "en" if ascii_ratio > 0.9 else "und"


def shingle(tokens: List[str], size: int = 3) -> List[str]:
    if len(tokens) < size:
        return ["_".join(tokens)] if tokens else []
    return ["_".join(tokens[i : i + size]) for i in range(len(tokens) - size + 1)]
