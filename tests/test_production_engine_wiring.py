"""The production registry must wire REAL engines and tell the truth about health.

This is the guard against the state that existed before: five fabricated-evidence
providers registered as if they were five engines, oracle and cypher implemented but
never registered, and every engine stamped HEALTHY regardless.
"""

from __future__ import annotations

import pytest

from abraxas.engines.manifest import LIVE, planned_engines
from abraxas.governance.production import EngineStatus, ProductionOrchestrator


@pytest.fixture
def orchestrator():
    instance = ProductionOrchestrator()
    instance.initialize()
    return instance


def test_real_engines_are_registered(orchestrator):
    from abraxas.engines.manifest import live_engines

    assert set(orchestrator.engine_registry.names()) == set(live_engines())


def test_oracle_and_cypher_are_registered(orchestrator):
    """Both were fully implemented and never registered."""
    registered = set(orchestrator.engine_registry.names())
    assert {"oracle", "cypher"} <= registered


def test_planned_engines_are_not_registered_as_providers(orchestrator):
    registered = set(orchestrator.engine_registry.names())
    assert registered.isdisjoint(set(planned_engines()))


def test_planned_engines_report_unhealthy_not_healthy(orchestrator):
    """Health must be able to say 'missing'."""
    for name in planned_engines():
        health = orchestrator.engine_registry.get_health(name)
        assert health is not None, f"{name} has no health entry at all"
        assert health.status == EngineStatus.UNHEALTHY, (
            f"{name} is unimplemented but reported {health.status.value}"
        )
        assert health.details.get("implemented") is False


def test_live_engines_report_healthy(orchestrator):
    from abraxas.engines.manifest import live_engines

    for name in live_engines():
        health = orchestrator.engine_registry.get_health(name)
        assert health is not None and health.status == EngineStatus.HEALTHY


def test_mocks_are_opt_in_only():
    """The fabricated-evidence path must be explicit, never the default."""
    instance = ProductionOrchestrator()
    instance.initialize(use_mocks=True)
    assert set(instance.engine_registry.names()), "mock path should still register"


def test_default_initialisation_does_not_register_mocks(orchestrator):
    assert "mock" not in orchestrator.engine_registry.names()
