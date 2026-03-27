from __future__ import annotations

from abx.explain.explainIrAudit import run_explain_ir_audit
from abx.explain.explainSerialization import serialize_explain_artifact, to_observability_explain
from abx.explain_ir import ExplainIR, ExplainProvenance
from abx.observability.scorecard import build_observability_health_scorecard
from abx.observability.summaryAssembly import build_observability_summary
from abx.observability.surfaceClassification import classify_surfaces, detect_redundant_surfaces
from abx.operator.insightAssembly import assemble_operator_insight_view
from abx.trace.causalTrace import build_causal_trace
from abx.trace.traceSummary import build_trace_summary


_LINKAGE = {
    "boundary_validation": "BoundaryValidationReport.v1",
    "trust_report": "BoundaryTrustReport.v1",
    "proof_chain": "ProofChainArtifact.v1",
    "closure_summary": "ClosureSummaryArtifact.v1",
}


def test_surface_classification_and_summary_are_stable() -> None:
    a = classify_surfaces()
    b = classify_surfaces()
    assert a == b
    assert isinstance(detect_redundant_surfaces(), list)

    s1 = build_observability_summary(run_id="RUN-1", linkage_refs=_LINKAGE)
    s2 = build_observability_summary(run_id="RUN-1", linkage_refs=_LINKAGE)
    assert s1 == s2


def test_explain_ir_coverage_and_serialization_are_deterministic() -> None:
    audit_a = run_explain_ir_audit()
    audit_b = run_explain_ir_audit()
    assert audit_a == audit_b

    ir = ExplainIR(
        explain_rune_id="rune.test",
        event_type="decision",
        summary="test",
        provenance=ExplainProvenance(observed=["o1"], inferred=["i1"], speculative=[]),
        confidence=0.8,
    )
    artifact, partition = to_observability_explain(ir)
    assert partition.observed_count == 1
    assert serialize_explain_artifact(artifact) == serialize_explain_artifact(artifact)


def test_causal_trace_and_summary_capture_degraded_points() -> None:
    trace_a = [x.__dict__ for x in build_causal_trace(run_id="RUN-1")]
    trace_b = [x.__dict__ for x in build_causal_trace(run_id="RUN-1")]
    assert trace_a == trace_b

    summary = build_trace_summary(run_id="RUN-1")
    assert summary.degraded_points
    assert summary.summary_hash


def test_operator_insight_view_is_deterministic_and_layered() -> None:
    a = assemble_operator_insight_view(run_id="RUN-1", linkage_refs=_LINKAGE)
    b = assemble_operator_insight_view(run_id="RUN-1", linkage_refs=_LINKAGE)
    assert a.__dict__ == b.__dict__
    assert "run_overview" in a.drilldown
    assert "causal_trace" in a.drilldown


def test_observability_scorecard_is_stable_and_surfaces_blockers() -> None:
    a = build_observability_health_scorecard(run_id="RUN-1", linkage_refs=_LINKAGE)
    b = build_observability_health_scorecard(run_id="RUN-1", linkage_refs=_LINKAGE)
    assert a.__dict__ == b.__dict__
    assert isinstance(a.blockers, list)
