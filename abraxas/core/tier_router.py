from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class TierProfile:
    name: str
    max_sources: int
    include_citations: bool
    scenario_branches: int
    market_depth: str  # "lite" | "standard" | "pro"
    memetics_depth: str  # "lite" | "standard" | "pro"
    aalmanac_depth: str  # "lite" | "standard" | "pro"
    neon_genie_depth: str  # "lite" | "standard" | "pro"


TIERS: Dict[str, TierProfile] = {
    "psychonaut": TierProfile(
        name="psychonaut",
        max_sources=12,
        include_citations=False,
        scenario_branches=1,
        market_depth="lite",
        memetics_depth="standard",
        aalmanac_depth="lite",
        neon_genie_depth="standard",
    ),
    "academic": TierProfile(
        name="academic",
        max_sources=30,
        include_citations=True,
        scenario_branches=2,
        market_depth="standard",
        memetics_depth="pro",
        aalmanac_depth="standard",
        neon_genie_depth="pro",
    ),
    "enterprise": TierProfile(
        name="enterprise",
        max_sources=60,
        include_citations=True,
        scenario_branches=4,
        market_depth="pro",
        memetics_depth="pro",
        aalmanac_depth="pro",
        neon_genie_depth="pro",
    ),
}


def tier_profile(tier: str) -> TierProfile:
    return TIERS.get(tier, TIERS["psychonaut"])


def tier_context(tier: str) -> Dict[str, Any]:
    """
    Deterministic, explicit knobs used by the oracle runner.
    These are NOT preferences; they are execution parameters.
    """
    tp = tier_profile(tier)
    return {
        "tier": tp.name,
        "limits": {"max_sources": tp.max_sources, "scenario_branches": tp.scenario_branches},
        "flags": {"include_citations": tp.include_citations},
        "depth": {
            "market": tp.market_depth,
            "memetics": tp.memetics_depth,
            "aalmanac": tp.aalmanac_depth,
            "neon_genie": tp.neon_genie_depth,
        },
    }
