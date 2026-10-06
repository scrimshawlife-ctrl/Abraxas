"""The registry must not present an unimplemented engine as an available one.

The canonical manifest deliberately keeps ``planned`` engines visible, and states the
rule explicitly: *"A ``planned`` engine must never be presented as available."*  That
distinction used to be erased at registration — every name, including ``aether`` (which
has zero files anywhere in the repo), was stamped ``REGISTERED`` and became
indistinguishable from a working provider.

These tests hold the line between two ideas that were the same object before:

* **addressable**  — the name is in the registry, so topology and tooling can see it
* **available**   — a real ``EvidenceProvider`` exists and it may produce evidence
"""

from __future__ import annotations

import pytest

from abraxas.evidence.contract import EvidenceEnvelope
from abraxas.engines.manifest import (
    COORDINATOR,
    TEST_DOUBLES,
    all_engine_names,
    live_engines,
    planned_engines,
    registrable_names,
)
from abraxas.yggdrasil.registry import (
    EngineStatus,
    YggdrasilEngineRegistry,
    status_for,
)

PINNED_CLOCK = "2026-01-01T00:00:00+00:00"


def _pinned(name: str = "test") -> str:
    return PINNED_CLOCK


def _rune(registry: YggdrasilEngineRegistry, name: str):
    """Fetch a rune, failing loudly instead of asserting on a None."""
    rune = registry.get_engine_rune(name)
    assert rune is not None, f"{name} is not registered"
    return rune


@pytest.fixture
def registry() -> YggdrasilEngineRegistry:
    """A registry populated exactly as the coordinator populates it."""
    from abraxas.yggdrasil.coordinator import YggdrasilCoordinator

    coordinator = YggdrasilCoordinator()
    coordinator._register_default_engines()
    return coordinator.rune_registry


# --------------------------------------------------------------------------
# lifecycle: the manifest's live/planned distinction must survive registration
# --------------------------------------------------------------------------


def test_live_engines_register_as_active(registry) -> None:
    for name in live_engines():
        rune = registry.get_engine_rune(name)
        assert rune is not None, f"{name} is not registered at all"
        assert rune.status == EngineStatus.ACTIVE, (
            f"{name} has a real provider but registered as {rune.status.value}"
        )


def test_planned_engines_register_as_planned(registry) -> None:
    for name in planned_engines():
        rune = registry.get_engine_rune(name)
        assert rune is not None, f"{name} should stay addressable"
        assert rune.status == EngineStatus.PLANNED, (
            f"{name} has no implementation but registered as {rune.status.value}"
        )


def test_planned_engines_are_addressable_but_not_available(registry) -> None:
    """The whole point: visible in the topology, unusable as an engine."""
    for name in planned_engines():
        assert registry.is_engine_registered(name), f"{name} lost addressability"
        assert not registry.is_engine_available(name), (
            f"{name} has no implementation but is offered as available"
        )


def test_aether_is_never_available(registry) -> None:
    """`aether` has zero files in the repo — the clearest possible case."""
    assert registry.is_engine_registered("aether")
    assert not registry.is_engine_available("aether")


def test_coordinator_and_test_doubles_are_not_available(registry) -> None:
    for name in (COORDINATOR, *TEST_DOUBLES):
        assert registry.is_engine_registered(name), f"{name} should be addressable"
        assert not registry.is_engine_available(name), (
            f"{name} is not an engine and must not be offered as one"
        )


def test_unknown_names_are_unavailable(registry) -> None:
    assert not registry.is_engine_available("no-such-engine")


def test_available_engines_agrees_with_the_manifest(registry) -> None:
    """The registry's own answer must match the canonical manifest."""
    assert set(registry.available_engines()) == set(live_engines())
    assert set(registry.planned_engines()) == set(planned_engines())


def test_every_registrable_name_has_a_lifecycle(registry) -> None:
    """No name may fall through to 'unknown behaviour'."""
    known = {EngineStatus.ACTIVE, EngineStatus.PLANNED, EngineStatus.REGISTERED}
    for name in registrable_names():
        status = status_for(name)
        assert status in known, f"{name} derived unexpected status {status}"


def test_registered_names_still_match_the_manifest(registry) -> None:
    """Regression guard for the pre-existing agreement contract."""
    assert set(registry.list_engines()) == set(registrable_names())


# --------------------------------------------------------------------------
# determinism: registration must not depend on the wall clock
# --------------------------------------------------------------------------


def test_registration_is_reproducible_with_a_pinned_clock() -> None:
    """Two registries with the same inputs must be identical.

    The coordinator used to put ``registered_at`` (a wall clock) in the metadata that
    feeds the rune hash, so the same engine hashed differently on every process start.
    """
    first = YggdrasilEngineRegistry(clock=_pinned)
    second = YggdrasilEngineRegistry(clock=_pinned)

    for name in all_engine_names():
        first.register_engine(name, {"evidence_type": "X"})
        second.register_engine(name, {"evidence_type": "X"})

    assert first.list_engines() == second.list_engines()
    for name in all_engine_names():
        a, b = _rune(first, name), _rune(second, name)
        assert a.rune_hash == b.rune_hash
        assert a.registered_at == PINNED_CLOCK


def test_rune_hash_is_metadata_key_order_independent() -> None:
    """The hash goes through the repo's canonical serializer, not a private one."""
    a = YggdrasilEngineRegistry(clock=_pinned)
    b = YggdrasilEngineRegistry(clock=_pinned)

    a.register_engine("athanor", {"evidence_type": "R", "implementation": "m:f"})
    b.register_engine("athanor", {"implementation": "m:f", "evidence_type": "R"})

    assert _rune(a, "athanor").rune_hash == _rune(b, "athanor").rune_hash


def test_rune_hash_changes_when_identity_changes() -> None:
    a = YggdrasilEngineRegistry(clock=_pinned)
    a.register_engine("athanor", {"evidence_type": "R"})
    a.register_engine("noesis", {"evidence_type": "R"})
    assert _rune(a, "athanor").rune_hash != _rune(a, "noesis").rune_hash


# --------------------------------------------------------------------------
# fail closed: the arbitration path must refuse an unavailable engine
# --------------------------------------------------------------------------


def _envelope(engine: str) -> EvidenceEnvelope:
    """A real envelope — every field on EvidenceEnvelope carries a default."""
    return EvidenceEnvelope(engine=engine, claim="a claim")


def test_coordinator_refuses_a_planned_engine() -> None:
    from abraxas.evidence.contract import Decision
    from abraxas.yggdrasil.coordinator import YggdrasilCoordinator

    coordinator = YggdrasilCoordinator()
    decision = coordinator.arbitrate_evidence(_envelope("aether"))
    assert decision == Decision.REJECT, (
        "a planned engine with no implementation was arbitrated instead of refused"
    )


def test_coordinator_refuses_an_unregistered_engine() -> None:
    from abraxas.evidence.contract import Decision
    from abraxas.yggdrasil.coordinator import YggdrasilCoordinator

    coordinator = YggdrasilCoordinator()
    decision = coordinator.arbitrate_evidence(_envelope("no-such-engine"))
    assert decision == Decision.REJECT
