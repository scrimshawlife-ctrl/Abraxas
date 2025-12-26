"""
Component Score Aggregation
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def aggregate_component_outcomes(
    outcomes: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Optional[float]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for outcome in outcomes:
        component_id = outcome["component_id"]
        grouped.setdefault(component_id, []).append(outcome)

    aggregated: Dict[str, Dict[str, Optional[float]]] = {}
    for component_id in sorted(grouped.keys()):
        component_outcomes = grouped[component_id]
        aggregated[component_id] = _aggregate_component(component_outcomes)

    return aggregated


def _aggregate_component(outcomes: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    total = len(outcomes)
    hits = sum(1 for o in outcomes if o["status"] == "HIT")
    misses = sum(1 for o in outcomes if o["status"] == "MISS")
    abstains = sum(1 for o in outcomes if o["status"] == "ABSTAIN")
    unknowns = sum(1 for o in outcomes if o["status"] == "UNKNOWN")

    brier_values = [
        o["score_contrib"]["brier"]
        for o in outcomes
        if o.get("score_contrib", {}).get("brier") is not None
    ]
    coverage_values = [
        o["score_contrib"]["coverage_rate"]
        for o in outcomes
        if o.get("score_contrib", {}).get("coverage_rate") is not None
    ]
    trend_values = [
        o["score_contrib"]["trend_acc"]
        for o in outcomes
        if o.get("score_contrib", {}).get("trend_acc") is not None
    ]

    denom = hits + misses
    hit_rate = hits / denom if denom > 0 else 0.0

    return {
        "n": total,
        "hit_rate": hit_rate,
        "brier_avg": _avg(brier_values),
        "coverage_rate": _avg(coverage_values),
        "trend_acc": _avg(trend_values),
        "abstain_rate": abstains / total if total else 0.0,
        "unknown_rate": unknowns / total if total else 0.0,
    }


def _avg(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)
