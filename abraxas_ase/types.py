from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class Item:
    id: str
    source: str
    url: str
    published_at: str  # ISO8601 string
    title: str
    text: str


@dataclass(frozen=True)
class TokenRec:
    token: str
    norm: str
    letters_sorted: str
    length: int
    unique_letters: int
    letter_entropy: float
    tap: float
    # provenance
    item_id: str
    source: str


@dataclass(frozen=True)
class SubAnagramHit:
    token: str
    sub: str
    tier: int  # 2
    verified: bool
    lane: str  # "core" | "canary"
    item_id: str
    source: str


@dataclass(frozen=True)
class ExactCollision:
    letters_sorted: str
    tokens: List[str]
    sources: List[str]
    item_ids: List[str]


@dataclass(frozen=True)
class PFDIAlert:
    key: str  # phrase-field key
    sub: str
    pfdi: float
    mentions_today: int
    baseline_mean: float
    baseline_std: float


JsonDict = Dict[str, Any]
