"""The governance layer decides whether evidence is trustworthy — it must not BE evidence.

`abraxas/governance/` owns arbitration. If it also *constructs* evidence naming an engine
that does not exist, then the layer that judges evidence is a source of fabricated
evidence, and nothing in the system can tell the difference.

Real defect this guards: `ProductionOrchestrator._process_stream_item` built an envelope
with `engine="stream"` — an engine that is not declared in the manifest and not registered
anywhere — from no provider at all. It was inert only BY ACCIDENT: `ProductionArbiter`
health-checks the engine first and returns ABSTAIN for unregistered names. Register that
name (or relax that gate) and fabricated evidence becomes decidable immediately, with
nothing else in the way.

Two guards, because each catches what the other cannot:

* a static scan of the layer, which catches the pattern anywhere in `abraxas/governance/`
  regardless of whether the code is reachable
* a behavioural check on the streaming path, which catches a violation that only appears
  at runtime
"""

from __future__ import annotations

import ast
import time
from pathlib import Path

import pytest

from abraxas.engines.manifest import (
    COORDINATOR,
    TEST_DOUBLES,
    all_engine_names,
)

GOVERNANCE_DIR = Path(__file__).resolve().parents[1] / "abraxas" / "governance"

#: A literal engine name is legitimate only if the architecture declares it. `mock` is a
#: declared test double and `yggdrasil` is the coordinator, so both are permitted by name —
#: the distinction that matters is that a literal is never invented inline.
ALLOWED_LITERAL_ENGINES = frozenset(
    all_engine_names() + TEST_DOUBLES + (COORDINATOR,)
)


def _evidence_envelope_engine_literals(path: Path):
    """Yield (line, engine_literal) for every EvidenceEnvelope(...) built in this file.

    Only string LITERALS are yielded. A name passed as a variable is not a violation —
    that is exactly how a real provider supplies its own identity.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name != "EvidenceEnvelope":
            continue
        for keyword in node.keywords:
            if keyword.arg != "engine":
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                yield node.lineno, keyword.value.value


def test_governance_layer_never_invents_an_engine_name() -> None:
    """Every literal engine name in a governance-built envelope must be declared.

    The arbitration layer may relay evidence. It must not mint an engine identity that
    the manifest does not know about.
    """
    violations = []
    for module in sorted(GOVERNANCE_DIR.glob("*.py")):
        for line, engine in _evidence_envelope_engine_literals(module):
            if engine not in ALLOWED_LITERAL_ENGINES:
                violations.append(f"{module.name}:{line} -> engine={engine!r}")

    assert violations == [], (
        "the governance layer constructed evidence naming an undeclared engine:\n  "
        + "\n  ".join(violations)
        + "\n\nRoute the evidence through a registered provider instead, or declare the "
          "engine in abraxas/engines/manifest.py."
    )


def test_governance_layer_has_exactly_one_evidence_construction_site() -> None:
    """The layer builds evidence in exactly one place, and it is the declared test double.

    Counted, not line-pinned: a line number would break on any unrelated edit above it and
    teach people to update the number without reading the assertion. A count is stable, and
    a new construction site still has to be acknowledged here.
    """
    sites = [
        f"{module.name}:{line}"
        for module in sorted(GOVERNANCE_DIR.glob("*.py"))
        for line, _ in _evidence_envelope_engine_literals(module)
    ]
    assert len(sites) == 1, (
        "expected exactly one evidence construction site in abraxas/governance, found "
        f"{len(sites)}: {sites}\n\nA new site means the arbitration layer has gained another "
        "way to build evidence. Route it through a registered provider instead."
    )
    assert sites[0].startswith("production.py:"), sites[0]


# --------------------------------------------------------------------------
# behavioural: the streaming path must relay provider evidence, not invent it
# --------------------------------------------------------------------------


@pytest.fixture
def orchestrator():
    from abraxas.governance.production import ProductionOrchestrator

    instance = ProductionOrchestrator()
    instance.initialize()  # real providers, resolved from the manifest
    return instance


def test_streaming_path_emits_evidence_from_registered_engines(orchestrator) -> None:
    """Whatever the streaming path produces must come from registered providers.

    Before the fix this path built its own envelope with `engine="stream"`, which the
    arbiter then abstained on — so streaming never decided anything, and the abstention
    was a side effect of an unregistered name rather than a design boundary.
    """
    registered = set(orchestrator.engine_registry.names())

    orchestrator.start_streaming_processor(num_workers=1)
    try:
        stream_id = orchestrator.submit_evidence_stream(
            "test-evidence-001", "A claim for the streaming path", {"test": "context"}
        )
        deadline = time.time() + 20.0
        result = None
        while time.time() < deadline:
            result = orchestrator.get_stream_result(stream_id, timeout=0.5)
            if result is not None:
                break
    finally:
        orchestrator.stop_streaming_processor()

    assert result is not None, "streaming produced no result at all"
    assert "error" not in result, f"streaming errored: {result.get('error')}"

    engines_used = result.get("engines_used")
    assert engines_used, (
        "streaming produced no engine attribution; evidence must be traceable to the "
        "engines that produced it"
    )
    unknown = sorted(set(engines_used) - registered)
    assert unknown == [], (
        f"streaming attributed evidence to unregistered engine(s): {unknown}"
    )


def test_streaming_records_abstention_when_no_engine_can_produce_evidence() -> None:
    """With no usable engine the honest outcome is ABSTAIN and no evidence — not a
    fabricated envelope that happens to look like evidence."""
    from abraxas.governance.production import EngineStatus, ProductionOrchestrator

    instance = ProductionOrchestrator()
    instance.initialize()
    # Simulate every provider becoming unusable.
    for name in list(instance.engine_registry.names()):
        instance.engine_registry.update_health(name, EngineStatus.UNHEALTHY)

    instance.start_streaming_processor(num_workers=1)
    try:
        stream_id = instance.submit_evidence_stream("ev-none", "a claim", {})
        deadline = time.time() + 20.0
        result = None
        while time.time() < deadline:
            result = instance.get_stream_result(stream_id, timeout=0.5)
            if result is not None:
                break
    finally:
        instance.stop_streaming_processor()

    assert result is not None
    assert result.get("engines_used") in (None, [], (),)
    assert result["decision"] == "ABSTAIN", (
        f"expected ABSTAIN with no usable engines, got {result['decision']!r}"
    )
