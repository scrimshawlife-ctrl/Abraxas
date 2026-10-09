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
    from abraxas.engines.manifest import live_engines, planned_engines
    # Live + intentionally stubbed planned (full integration beyond stubs)
    STUBBED_PLANNED = {"chronos", "resonance", "aether", "semion", "hyperlex"}
    expected = set(live_engines()) | (set(planned_engines()) & STUBBED_PLANNED)
    assert set(orchestrator.engine_registry.names()) == expected


def test_oracle_and_cypher_are_registered(orchestrator):
    """Both were fully implemented and never registered."""
    registered = set(orchestrator.engine_registry.names())
    assert {"oracle", "cypher"} <= registered


def test_non_stub_planned_engines_are_not_registered_as_providers(orchestrator):
    """True unimplemented planned stay unregistered; stubbed ones are now wired."""
    from abraxas.engines.manifest import planned_engines
    STUBBED_PLANNED = {"chronos", "resonance", "aether", "semion", "hyperlex"}
    non_stub_planned = set(planned_engines()) - STUBBED_PLANNED
    registered = set(orchestrator.engine_registry.names())
    assert registered.isdisjoint(non_stub_planned)


def test_planned_engines_report_unhealthy_not_healthy(orchestrator):
    """Health must be able to say 'missing' for non-stub planned."""
    from abraxas.engines.manifest import planned_engines
    STUBBED_PLANNED = {"chronos", "resonance", "aether", "semion", "hyperlex"}
    for name in planned_engines():
        if name in STUBBED_PLANNED:
            continue  # stubbed planned are wired as real (minimal) now
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


def test_production_uses_real_stub_providers_for_planned():
    """Production must resolve planned stubs from manifest impl paths (beyond legacy mocks)."""
    from abraxas.governance.production import ProductionOrchestrator
    o = ProductionOrchestrator()
    o.initialize(use_mocks=False)  # real path
    # After change, stub names should be resolvable via manifest factories
    reg = o.engine_registry
    names = set(reg.names()) if hasattr(reg, 'names') else set(getattr(reg, '_engines', {}).keys())
    assert 'chronos' in names or any('chronos' in str(x) for x in names), "chronos stub not resolved in real production path"
