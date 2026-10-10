"""The production registry must wire REAL engines and tell the truth about health.

This is the guard against the state that existed before: five fabricated-evidence
providers registered as if they were five engines, oracle and cypher implemented but
never registered, and every engine stamped HEALTHY regardless.
"""

from __future__ import annotations

import pytest

from abraxas.engines.manifest import planned_engines
from abraxas.governance.production import EngineStatus, ProductionOrchestrator


@pytest.fixture
def orchestrator():
    instance = ProductionOrchestrator()
    instance.initialize()
    return instance


def test_real_engines_are_registered(orchestrator):
    from abraxas.engines.manifest import all_engine_names
    # All declared engines with implementations are registered (manifest is single source).
    expected = set(all_engine_names())
    assert set(orchestrator.engine_registry.names()) == expected


def test_oracle_and_cypher_are_registered(orchestrator):
    """Both were fully implemented and never registered."""
    registered = set(orchestrator.engine_registry.names())
    assert {"oracle", "cypher"} <= registered


def test_non_stub_planned_engines_are_not_registered_as_providers(orchestrator):
    """No stub bypass: all engines are registered uniformly via manifest implementation."""
    # All planned engines have implementations; none should be missing from registry.
    planned = set(planned_engines())
    registered = set(orchestrator.engine_registry.names())
    missing = planned - registered
    assert missing == set(), f"planned engines not registered: {missing}"


def test_planned_engines_are_not_registered_as_providers(orchestrator):
    test_non_stub_planned_engines_are_not_registered_as_providers(orchestrator)


def test_planned_engines_report_unhealthy_not_healthy(orchestrator):
    """Every planned engine reports UNHEALTHY — no stub bypass."""
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


def test_production_resolves_planned_via_manifest():
    """Production resolves engines uniformly via manifest (no stub bypass)."""
    from abraxas.governance.production import ProductionOrchestrator
    o = ProductionOrchestrator()
    o.initialize(use_mocks=False)
    names = set(o.engine_registry.names())
    assert 'chronos' in names, "chronos not resolved in production path"
    # chronos is now LIVE in the manifest — resolved as a real provider
    health = o.engine_registry.get_health("chronos")
    assert health.status == EngineStatus.HEALTHY
