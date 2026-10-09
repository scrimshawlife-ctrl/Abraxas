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
    topology drifted in the first place.
    Exception: the intentional minimal stubs we added for chronos/resonance/aether
    per manifest + ENGINE_TOPOLOGY.md are allowed as planned stubs."""
    claiming = sorted(
        spec.name
        for spec in ENGINES
        if spec.status == PLANNED
        and spec.implementation
        and spec.name not in ("chronos", "resonance", "aether", "semion", "hyperlex")
    )
    assert claiming == [], f"planned engines claiming an implementation: {claiming}"


def _resolve(spec):
    """Resolve ``module:Attribute``. Importing the module is NOT enough —
    an earlier version of this test did only that and therefore passed while the
    manifest claimed a class that was factory-local and did not exist."""
    module_path, attribute = spec.implementation.split(":", 1)
    module = importlib.import_module(module_path)
    assert hasattr(module, attribute), (
        f"{spec.name}: {module_path} has no attribute {attribute!r}. "
        f"Declare the real entry point (a factory function is fine)."
    )
    return getattr(module, attribute)


def _provider(spec):
    """Resolve the engine's actual EvidenceProvider: the class itself, or a factory
    called with the minimal stand-in its signature needs.

    Extracted so the conformance test, the envelope test and the evidence-type test
    all resolve providers the SAME way. Three copies of this logic would drift, and
    the one that drifted would be the one deciding what "the engine" means.
    """
    import inspect

    target = _resolve(spec)
    if isinstance(target, type):
        return target()
    params = inspect.signature(target).parameters
    kwargs = {}
    if "inference_engine" in params:
        # Some engines wrap an external inference callable (that is the design: the
        # engine owns reasoning, Abraxas owns arbitration), so supply a minimal stand-in.
        kwargs["inference_engine"] = lambda claim, context: {
            "candidates": [],
            "model_identity": "stub",
            "relations": [],
            "reasoning_steps": [],
            "provenance": {},
        }
    return target(**kwargs)


@pytest.mark.parametrize("spec", LIVE_SPECS, ids=lambda spec: spec.name)
def test_live_engine_entry_point_resolves(spec) -> None:
    """Every engine marked live must have a resolvable, callable entry point."""
    target = _resolve(spec)
    assert callable(target), f"{spec.name}: entry point is not callable"


@pytest.mark.parametrize("spec", LIVE_SPECS, ids=lambda spec: spec.name)
def test_live_engine_entry_point_conforms_to_the_provider_interface(spec) -> None:
    """A live engine must be an EvidenceProvider subclass, or a factory that
    returns one. This is the boundary the architecture depends on:
    Abraxas owns arbitration, engines own reasoning."""
    from abraxas.evidence.provider import EvidenceProvider

    target = _resolve(spec)
    if isinstance(target, type):
        assert issubclass(target, EvidenceProvider), (
            f"{spec.name}: {target.__name__} does not subclass EvidenceProvider"
        )
        return
    # A factory. Some wrap an external inference callable (that is the design:
    # the engine owns reasoning, Abraxas owns arbitration), so supply a minimal
    # stand-in when the signature requires one.
    import inspect

    params = inspect.signature(target).parameters
    kwargs = {}
    if "inference_engine" in params:
        kwargs["inference_engine"] = lambda claim, context: {
            "candidates": [],
            "model_identity": "stub",
            "relations": [],
            "reasoning_steps": [],
            "provenance": {},
        }
    produced = target(**kwargs)
    assert isinstance(produced, EvidenceProvider), (
        f"{spec.name}: factory returned {type(produced).__name__}, "
        f"not an EvidenceProvider"
    )


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


def test_every_engine_declares_its_three_settlements() -> None:
    from abraxas.engines.manifest import ENGINES
    from abraxas.engines.settlement import SETTLEMENT_VALUES

    bad = [
        spec.name
        for spec in ENGINES
        if any(
            getattr(spec.settlements, s) not in SETTLEMENT_VALUES
            for s in ("empirical", "technical", "economic")
        )
    ]
    assert bad == [], f"engines declaring an unknown settlement value: {bad}"


def test_a_settled_settlement_must_cite_evidence() -> None:
    """A settlement field will go unfilled unless something forces it -- and a 'settled' claim
    with no evidence is worse than 'unsettled'."""
    from abraxas.engines.manifest import ENGINES

    empty = [
        f"{spec.name}.{name}"
        for spec in ENGINES
        for name in ("empirical", "technical", "economic")
        if getattr(spec.settlements, name) == "settled"
        and not getattr(spec.settlements, f"{name}_evidence")
    ]
    assert empty == [], f"settled without evidence: {empty}"


@pytest.mark.parametrize("spec", LIVE_SPECS, ids=lambda spec: spec.name)
def test_live_engine_produce_evidence_returns_the_canonical_envelope(spec) -> None:
    """Every LIVE engine must return an EvidenceEnvelope from produce_evidence,
    not a bare dict or any other type. The boundary states: Abraxas owns
    arbitration, engines own reasoning, and the envelope is the contract at
    that boundary."""
    from abraxas.evidence.contract import EvidenceEnvelope

    provider = _provider(spec)

    result = provider.produce_evidence(
        request_id="guard-001",
        claim="Does this engine return the canonical envelope?",
        context={},
    )
    assert isinstance(result, EvidenceEnvelope), (
        f"{spec.name}: produce_evidence returned {type(result).__name__}, "
        f"not EvidenceEnvelope"
    )


def test_a_planned_engine_claims_no_empirical_settlement() -> None:
    """Extends the manifest's own invariant: a planned engine must not be presented as available,
    and empirical settlement is the strongest claim there is."""
    from abraxas.engines.manifest import ENGINES, PLANNED

    claiming = [
        spec.name
        for spec in ENGINES
        if spec.status == PLANNED and spec.settlements.empirical == "settled"
    ]
    assert claiming == [], f"planned engines claiming empirical settlement: {claiming}"


def test_settlement_evidence_references_resolve() -> None:
    """Every evidence reference is a repo-relative path that exists."""
    from pathlib import Path

    from abraxas.engines.manifest import ENGINES

    repo = Path(__file__).resolve().parents[1]
    missing = [
        ref
        for spec in ENGINES
        for name in ("empirical", "technical", "economic")
        for ref in getattr(spec.settlements, f"{name}_evidence")
        if not (repo / ref).exists()
    ]
    assert missing == [], f"settlement evidence pointing at nothing: {missing}"


@pytest.mark.parametrize("spec", LIVE_SPECS, ids=lambda spec: spec.name)
def test_live_engine_declared_evidence_type_matches_what_it_produces(spec) -> None:
    """The manifest's DECLARED evidence_type must match the type the engine actually emits.

    Why this guard exists
    ---------------------
    The manifest is the single source of truth for engine TOPOLOGY, and its stated purpose is to stop
    the engine list from disagreeing with itself. Its ``evidence_type`` field was never checked against
    the engines it describes, and two entries had drifted: ``oracle`` and ``cypher`` both declared
    ``RELATIONAL_REASONING`` while their providers emit ``NARRATIVE_SYNTHESIS`` and
    ``PERSISTENT_MEMORY``.

    The value they carried is the tell: ``RELATIONAL_REASONING`` is the ``EvidenceEnvelope`` dataclass
    DEFAULT, so a declaration that was never filled in looks exactly like one considered and chosen. A
    default standing in for a decision is the class of drift this file exists to prevent, one field over.

    The neighbouring test asserts a live engine returns the canonical ENVELOPE. It does not assert the
    envelope's TYPE, so it stayed green while the declaration was wrong — a shape guard verifying that a
    field is present without ever checking what it says.
    """
    produced = _provider(spec).produce_evidence(
        request_id="guard-002",
        claim="Does this engine emit the evidence type the manifest declares?",
        context={},
    )
    declared, actual = spec.evidence_type, produced.evidence_type.value
    assert declared == actual, (
        f"{spec.name}: the manifest declares evidence_type={declared!r} but the engine emits "
        f"{actual!r}. The manifest describes the engines that exist — when the code moves, the "
        f"declaration moves with it."
    )


def test_chronos_provider_minimal():
    """Chronos must have a minimal provider that satisfies basic interface (even while PLANNED)."""
    from abraxas.evidence.providers.chronos import create_chronos_adapter
    p = create_chronos_adapter()
    assert p.engine_name == "chronos"
    env = p.produce_evidence("req1", "test claim", {})
    assert env.engine == "chronos"


def test_resonance_provider_minimal():
    """Resonance must have a minimal provider that satisfies basic interface (even while PLANNED)."""
    from abraxas.evidence.providers.resonance import create_resonance_adapter
    p = create_resonance_adapter()
    assert p.engine_name == "resonance"
    env = p.produce_evidence("req1", "test claim", {})
    assert env.engine == "resonance"


def test_aether_provider_minimal():
    """Aether must have a minimal provider that raises per manifest design."""
    from abraxas.evidence.providers.aether import create_aether_adapter
    p = create_aether_adapter()
    assert p.engine_name == "aether"
    try:
        p.produce_evidence("req1", "test claim", {})
    except NotImplementedError:
        pass
    else:
        assert False, "Aether should raise NotImplementedError"
