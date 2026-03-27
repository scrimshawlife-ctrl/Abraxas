from __future__ import annotations

from abx.observability.types import CausalTraceRecord


_TRACE_STEPS = [
    ("input_envelope", "transforms_to", "boundary_validation", "VALID"),
    ("boundary_validation", "classifies", "trust_enforcement", "VALID"),
    ("trust_enforcement", "gates", "runtime_execution", "DEGRADED"),
    ("runtime_execution", "emits", "proof_chain", "VALID"),
    ("proof_chain", "closes", "closure_summary", "VALID"),
]


def build_causal_trace(*, run_id: str) -> list[CausalTraceRecord]:
    rows = [
        CausalTraceRecord(
            trace_id=f"trace-{run_id}-{idx}",
            run_id=run_id,
            step=step,
            relation=relation,
            evidence_ref=evidence,
            state=state,
        )
        for idx, (step, relation, evidence, state) in enumerate(_TRACE_STEPS)
    ]
    return rows
