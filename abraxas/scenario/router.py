"""Scenario Router.

Deterministic routing for scenario envelopes based on domain + priority rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


PRIORITY_WEIGHT = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


@dataclass(frozen=True)
class RoutingDecision:
    scenario_id: str
    domain: str
    priority: str
    handler_assigned: str
    routing_time_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "domain": self.domain,
            "priority": self.priority,
            "handler_assigned": self.handler_assigned,
            "routing_time_ms": self.routing_time_ms,
        }


def _priority_value(priority: str) -> int:
    return PRIORITY_WEIGHT.get(priority.lower(), 0)


def _select_rule(
    domain: str,
    priority: str,
    routing_rules: Iterable[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    candidates = [
        rule
        for rule in routing_rules
        if str(rule.get("domain") or "").upper() == domain
        and (rule.get("priority") is None or str(rule.get("priority") or "").lower() == priority)
    ]
    if not candidates:
        candidates = [
            rule for rule in routing_rules if str(rule.get("domain") or "").upper() == domain
        ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda rule: (
            _priority_value(str(rule.get("priority") or priority)),
            float(rule.get("confidence", 0.0)),
        ),
        reverse=True,
    )
    return candidates[0]


def _resolve_handler(
    rule: Optional[Dict[str, Any]],
    handler_registry: Dict[str, Any],
) -> str:
    if rule:
        handler_id = str(rule.get("handler") or "")
        if handler_id and handler_id in handler_registry:
            return handler_id
    if "default" in handler_registry:
        return "default"
    if handler_registry:
        return sorted(handler_registry.keys())[0]
    return "unassigned"


def route_scenario_envelope(
    *,
    scenario_envelope: Dict[str, Any],
    routing_rules: Iterable[Dict[str, Any]],
    handler_registry: Dict[str, Any],
) -> Tuple[RoutingDecision, float]:
    """
    Route a single scenario envelope to a handler.

    Returns routing decision and confidence score used for aggregate accuracy.
    """
    scenario_id = str(scenario_envelope.get("scenario_id") or scenario_envelope.get("id") or "unknown")
    domain = str(scenario_envelope.get("domain") or "UNKNOWN").upper()
    priority = str(scenario_envelope.get("priority") or "medium").lower()

    rule = _select_rule(domain, priority, routing_rules)
    handler_assigned = _resolve_handler(rule, handler_registry)

    priority_weight = _priority_value(priority)
    base_time = int(rule.get("base_time_ms", 2 + priority_weight)) if rule else 2 + priority_weight
    routing_time_ms = max(1, base_time)
    confidence = float(rule.get("confidence", 0.9)) if rule else 0.75

    decision = RoutingDecision(
        scenario_id=scenario_id,
        domain=domain,
        priority=priority,
        handler_assigned=handler_assigned,
        routing_time_ms=routing_time_ms,
    )
    return decision, confidence


def route_scenarios(
    *,
    scenario_envelopes: List[Dict[str, Any]],
    routing_rules: Iterable[Dict[str, Any]],
    handler_registry: Dict[str, Any],
) -> Dict[str, Any]:
    """Route multiple envelopes and compute aggregate routing accuracy."""
    decisions: List[RoutingDecision] = []
    confidences: List[float] = []
    for envelope in scenario_envelopes:
        decision, confidence = route_scenario_envelope(
            scenario_envelope=envelope,
            routing_rules=routing_rules,
            handler_registry=handler_registry,
        )
        decisions.append(decision)
        confidences.append(confidence)

    total = len(decisions)
    avg_conf = sum(confidences) / total if total else 0.0
    routing_accuracy = round(avg_conf, 2)

    return {
        "routing_decisions": [decision.to_dict() for decision in decisions],
        "routing_accuracy": routing_accuracy,
        "total_routed": total,
    }


__all__ = ["route_scenario_envelope", "route_scenarios", "RoutingDecision"]
