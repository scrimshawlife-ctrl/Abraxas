from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Literal


ChannelKind = Literal[
    "news",
    "social",
    "video",
    "forums",
    "markets",
    "gov",
    "research",
    "local",
    "custom",
]
AcqMode = Literal["decodo", "direct_http", "rss", "manual_offline"]


@dataclass(frozen=True)
class VectorChannel:
    id: str
    kind: ChannelKind
    mode: AcqMode
    enabled: bool
    weight: float
    domains: List[str]
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


def default_vector_map_v0_1() -> Dict:
    """
    Deterministic default map. Users can override with a JSON file later.
    No live URLs required; domains are sufficient for controlled search.
    """
    channels = [
        VectorChannel(
            id="news_general",
            kind="news",
            mode="decodo",
            enabled=True,
            weight=1.0,
            domains=[],
            notes="General news sweep (broad).",
        ),
        VectorChannel(
            id="news_finance",
            kind="news",
            mode="decodo",
            enabled=True,
            weight=0.8,
            domains=["wsj.com", "ft.com", "reuters.com", "bloomberg.com"],
            notes="Higher credibility finance/news.",
        ),
        VectorChannel(
            id="gov_sources",
            kind="gov",
            mode="decodo",
            enabled=True,
            weight=0.9,
            domains=[".gov"],
            notes="Government domains when relevant.",
        ),
        VectorChannel(
            id="research",
            kind="research",
            mode="decodo",
            enabled=True,
            weight=0.7,
            domains=["arxiv.org", "nature.com", "science.org", "pubmed.ncbi.nlm.nih.gov"],
            notes="Research confirmation paths.",
        ),
        VectorChannel(
            id="forums",
            kind="forums",
            mode="decodo",
            enabled=True,
            weight=0.6,
            domains=["reddit.com", "news.ycombinator.com"],
            notes="Community signal; high noise.",
        ),
        VectorChannel(
            id="video",
            kind="video",
            mode="decodo",
            enabled=False,
            weight=0.4,
            domains=["youtube.com", "tiktok.com"],
            notes="Optional; heavier extraction.",
        ),
        VectorChannel(
            id="local_offline",
            kind="local",
            mode="manual_offline",
            enabled=True,
            weight=1.0,
            domains=[],
            notes="User uploads, notes, screenshots, private corpus.",
        ),
    ]
    return {
        "version": "vector_map.v0.1",
        "channels": [c.to_dict() for c in channels],
        "policy": {
            "decodo_primary": True,
            "fallback_enabled": True,
            "offline_allowed": True,
        },
    }
