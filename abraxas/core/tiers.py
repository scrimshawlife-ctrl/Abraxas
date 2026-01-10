from __future__ import annotations
from typing import Dict, Any


ORACLE_TIER_RULES: Dict[str, Dict[str, Any]] = {
    "psychonaut": {
        "metrics": ["interpretive", "symbolic", "narrative"],
        "quantification": "low",
        "sources": "public+symbolic",
        "simulation": False,
        "overlays_allowed": ["aalmanac"],  # default safe set
        "admin_projection": False,
    },
    "academic": {
        "metrics": ["defined", "comparative", "time-series"],
        "quantification": "medium",
        "sources": "public+academic",
        "simulation": "limited",
        "overlays_allowed": ["aalmanac", "beatoven"],
        "admin_projection": False,
    },
    "enterprise": {
        "metrics": ["quantified", "predictive", "scenario"],
        "quantification": "high",
        "sources": "full",
        "simulation": True,
        "overlays_allowed": ["aalmanac", "beatoven", "neon_genie"],
        "admin_projection": False,  # still admin-only
    },
}


def tier_rules(tier: str) -> Dict[str, Any]:
    if tier not in ORACLE_TIER_RULES:
        raise ValueError(f"Unknown tier: {tier}")
    return ORACLE_TIER_RULES[tier]


def enforce_overlay_allowed(tier: str, overlay_name: str) -> None:
    allowed = set(tier_rules(tier).get("overlays_allowed", []))
    if overlay_name not in allowed:
        raise PermissionError(f"Overlay '{overlay_name}' not allowed for tier '{tier}'")
