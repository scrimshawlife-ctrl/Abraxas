"""End-to-end coverage of the production arbitration path.

Before this existed, the orchestrator ran entirely on `_mock_evidence` and NOTHING
asserted on its output -- which is why swapping in five real providers changed the
suite by exactly zero. Real engines are now wired; these tests verify the decisions
they actually produce.
"""

from __future__ import annotations

import pytest

from abraxas.engines.manifest import live_engines
from abraxas.governance.production import ProductionOrchestrator

CLAIM = "The algorithm promotes engagement bait through a manufactured consensus."
KNOWN_DECISIONS = {"VERIFY", "REJECT", "DEFER", "ABSTAIN", "ESCALATE"}


@pytest.fixture(scope="module")
def pipeline_result():
    orchestrator = ProductionOrchestrator()
    orchestrator.initialize()
    return orchestrator.run_pipeline(CLAIM)


def test_pipeline_produces_a_decision(pipeline_result):
    assert pipeline_result["decision"], "pipeline returned no decision"
    assert pipeline_result["decision"] in KNOWN_DECISIONS, (
        f"unexpected decision value: {pipeline_result['decision']}"
    )


def test_evidence_comes_from_real_engines(pipeline_result):
    used = set(pipeline_result["engines_used"])
    assert used, "no engines contributed evidence"
    from abraxas.engines.manifest import live_engines, planned_engines
    STUBBED = {"chronos", "resonance", "aether", "semion", "hyperlex"}
    allowed = set(live_engines()) | (set(planned_engines()) & STUBBED)
    assert used <= allowed, (
        f"evidence came from engines that are not live or stubbed: {sorted(used - allowed)}"
    )


def test_no_engine_reports_itself_as_a_mock(pipeline_result):
    """The strongest guard: fabricated evidence must not reappear silently."""
    assert "mock" not in pipeline_result["engines_used"]
    for envelope in pipeline_result.get("envelopes", []) or []:
        provenance = getattr(envelope, "provenance", None) or {}
        assert provenance.get("mock") is not True, "a mock envelope reached arbitration"


def test_one_envelope_per_contributing_engine(pipeline_result):
    assert pipeline_result["evidence_count"] == len(pipeline_result["engines_used"])


def test_governance_gates_ran(pipeline_result):
    details = pipeline_result["governance_details"]
    assert isinstance(details.get("aggregate_score"), (int, float))
    assert details.get("gate_results"), "no governance gate results recorded"


def test_governance_score_is_a_probability(pipeline_result):
    score = pipeline_result["governance_score"]
    assert 0.0 <= score <= 1.0, f"governance_score out of range: {score}"


def test_pipeline_is_deterministic_for_a_given_claim():
    """With the model-agnostic offline adapter the whole path should be stable.

    request_id embeds a millisecond timestamp, so compare the decision-bearing
    fields rather than the whole payload.
    """
    orchestrator = ProductionOrchestrator()
    orchestrator.initialize()
    first = orchestrator.run_pipeline(CLAIM)
    second = orchestrator.run_pipeline(CLAIM)
    assert first["decision"] == second["decision"]
    assert first["engines_used"] == second["engines_used"]
    assert first["governance_score"] == second["governance_score"]


def test_different_claims_are_handled():
    orchestrator = ProductionOrchestrator()
    orchestrator.initialize()
    other = orchestrator.run_pipeline("A completely unrelated claim about rainfall totals.")
    assert other["decision"] in KNOWN_DECISIONS
    assert other["evidence_count"] > 0
