from __future__ import annotations

from abx.explain.explainIrCoverage import build_explain_coverage
from abx.observability.summaryAssembly import build_observability_summary
from abx.observability.surfaceClassification import detect_redundant_surfaces
from abx.observability.types import ObservabilityHealthScorecard
from abx.trace.traceCoverage import build_trace_coverage
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_observability_health_scorecard(*, run_id: str, linkage_refs: dict[str, str]) -> ObservabilityHealthScorecard:
    summary = build_observability_summary(run_id=run_id, linkage_refs=linkage_refs)
    explain = build_explain_coverage()
    trace_coverage = build_trace_coverage(run_id=run_id)
    redundant = detect_redundant_surfaces()

    dimensions = {
        "observability_coverage": "COVERED" if bool(summary["surfaceClassification"]) else "PARTIAL",
        "explain_ir_coverage": "COVERED" if all(x.coverage_status != "GAP" for x in explain) else "PARTIAL",
        "provenance_partition_coverage": "COVERED" if all(x.coverage_status == "COVERED" for x in explain) else "PARTIAL",
        "causal_trace_coverage": "COVERED" if not trace_coverage.missing_surfaces else "PARTIAL",
        "operator_view_coherence": "COVERED",
        "duplicate_surface_burden": "PARTIAL" if redundant else "COVERED",
        "degraded_state_visibility": "COVERED",
        "boundary_trust_visibility": "COVERED" if "boundary_validation" in linkage_refs else "PARTIAL",
        "closure_proof_visibility": "COVERED" if "proof_chain" in linkage_refs else "PARTIAL",
    }
    evidence = {
        "summary": [str(summary["summaryHash"])],
        "explain": [x.surface_id for x in explain],
        "trace": trace_coverage.traceable_surfaces,
        "linkage": sorted(linkage_refs.keys()),
    }
    blockers = sorted([k for k, v in dimensions.items() if v == "PARTIAL"])
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers}
    score_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return ObservabilityHealthScorecard(
        artifact_type="ObservabilityHealthScorecard.v1",
        artifact_id=f"observability-health-{run_id}",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=score_hash,
    )
