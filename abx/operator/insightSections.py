from __future__ import annotations

from abx.trace.traceSummary import build_trace_summary


def build_insight_sections(*, run_id: str, linkage_refs: dict[str, str]) -> dict[str, dict[str, object]]:
    trace = build_trace_summary(run_id=run_id)
    return {
        "run_overview": {"run_id": run_id, "linkedArtifacts": sorted(linkage_refs.keys())},
        "proof_validation_closure": {
            "proof_chain": linkage_refs.get("proof_chain", "missing"),
            "closure_summary": linkage_refs.get("closure_summary", "missing"),
        },
        "boundary_trust": {
            "boundary_validation": linkage_refs.get("boundary_validation", "missing"),
            "trust_report": linkage_refs.get("trust_report", "missing"),
        },
        "causal_trace": {
            "steps": trace.steps,
            "degraded_points": trace.degraded_points,
        },
    }
