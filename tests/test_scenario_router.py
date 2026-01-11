from __future__ import annotations

import json
from pathlib import Path

from abraxas.scenario.router import route_scenarios


def test_routing_logic():
    routing_rules = [
        {
            "domain": "TAU",
            "priority": "high",
            "handler": "tau_handler",
            "base_time_ms": 5,
            "confidence": 0.99,
        },
        {
            "domain": "MW",
            "priority": "medium",
            "handler": "mw_handler",
            "base_time_ms": 3,
            "confidence": 0.97,
        },
    ]
    handler_registry = {"tau_handler": {}, "mw_handler": {}, "default": {}}
    scenario_envelopes = [
        {"scenario_id": "scenario_001", "domain": "TAU", "priority": "high"},
        {"scenario_id": "scenario_002", "domain": "MW", "priority": "medium"},
    ]

    report = route_scenarios(
        scenario_envelopes=scenario_envelopes,
        routing_rules=routing_rules,
        handler_registry=handler_registry,
    )

    golden_path = Path("tests/golden/operators/scenario_router_decisions.json")
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    assert report == expected


def test_routing_priority():
    routing_rules = [
        {"domain": "TAU", "priority": "low", "handler": "tau_low", "base_time_ms": 4},
        {"domain": "TAU", "priority": "high", "handler": "tau_high", "base_time_ms": 2},
    ]
    handler_registry = {"tau_low": {}, "tau_high": {}, "default": {}}
    scenario_envelopes = [{"scenario_id": "scenario_003", "domain": "TAU", "priority": "high"}]

    report = route_scenarios(
        scenario_envelopes=scenario_envelopes,
        routing_rules=routing_rules,
        handler_registry=handler_registry,
    )

    decision = report["routing_decisions"][0]
    assert decision["handler_assigned"] == "tau_high"
    assert decision["routing_time_ms"] == 2
