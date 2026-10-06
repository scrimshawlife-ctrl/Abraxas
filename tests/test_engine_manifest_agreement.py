"""Agreement guard for the canonical engine topology.

The engine list used to live in three places that disagreed: Yggdrasil's
coordinator, the production registry, and what was actually implemented. These
tests make a silent divergence impossible to reintroduce — the same idea as
tests/test_coupling_lint.py's ratchet, applied to the engine topology.
"""

from __future__ import annotations

import importlib

import pytest

from abraxas.engines.manifest import (
    COORDINATOR,
    ENGINES,
    LIVE,
    PLANNED,
    TEST_DOUBLES,
    all_engine_names,
    live_engines,
    planned_engines,
    registrable_names,
)

LIVE_SPECS = [spec for spec in ENGINES if spec.status == LIVE]


def test_manifest_has_no_duplicate_engine_names() -> None:
    names = all_engine_names()
    assert len(names) == len(set(names)), f"duplicate engine names in manifest: {names}"


def test_every_engine_has_a_known_status() -> None:
    unknown = sorted({spec.status for spec in ENGINES} - {LIVE, PLANNED})
    assert unknown == [], f"unknown engine status: {unknown}"


def test_live_engines_declare_an_implementation() -> None:
    missing = sorted(spec.name for spec in LIVE_SPECS if not spec.implementation)
    assert missing == [], f"live engines with no implementation declared: {missing}"


def test_planned_engines_declare_no_implementation() -> None:
    """A planned engine must not claim an implementation — that is how the
    topology drifted in the first place."""
    claiming = sorted(
        spec.name for spec in ENGINES if spec.status == PLANNED and spec.implementation
    )
    assert claiming == [], f"planned engines claiming an implementation: {claiming}"


@pytest.mark.parametrize("spec", LIVE_SPECS, ids=lambda spec: spec.name)
def test_live_engine_implementation_is_importable(spec) -> None:
    """Every engine marked live must actually import."""
    module_path = spec.implementation.split(":", 1)[0]
    importlib.import_module(module_path)


def test_coordinator_registers_exactly_the_manifest() -> None:
    """Yggdrasil must register the manifest, not a private literal."""
    from abraxas.yggdrasil.coordinator import YggdrasilCoordinator

    coordinator = YggdrasilCoordinator()
    coordinator._register_default_engines()

    registered = set(coordinator.rune_registry.list_engines())
    expected = set(registrable_names())

    assert registered == expected, (
        f"coordinator/rune-registry disagreement.\n"
        f"  registered but not in manifest: {sorted(registered - expected)}\n"
        f"  in manifest but not registered: {sorted(expected - registered)}"
    )


def test_coordinator_is_not_declared_as_an_engine() -> None:
    assert COORDINATOR not in all_engine_names()
    assert COORDINATOR in registrable_names()


def test_test_doubles_are_not_declared_as_engines() -> None:
    """'mock' is a test double; it must never be presented as an engine."""
    for double in TEST_DOUBLES:
        assert double not in all_engine_names()
        assert double in registrable_names()


def test_production_registry_names_are_all_known() -> None:
    """Whatever production registers must at least be a declared engine."""
    from abraxas.governance.production import ProductionOrchestrator

    orchestrator = ProductionOrchestrator()
    orchestrator.initialize()

    declared = set(all_engine_names())
    registered = set(orchestrator.engine_registry.names())

    unknown = sorted(registered - declared)
    assert unknown == [], f"production registers undeclared engines: {unknown}"


def test_live_and_planned_partition_the_manifest() -> None:
    assert set(live_engines()) | set(planned_engines()) == set(all_engine_names())
    assert set(live_engines()) & set(planned_engines()) == set()
