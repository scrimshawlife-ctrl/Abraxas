from __future__ import annotations

from abx.observability.types import TraceCoverageRecord
from abx.trace.causalTrace import build_causal_trace


_EXPECTED = {"input_envelope", "boundary_validation", "trust_enforcement", "runtime_execution", "proof_chain"}


def build_trace_coverage(*, run_id: str) -> TraceCoverageRecord:
    seen = {x.step for x in build_causal_trace(run_id=run_id)}
    missing = sorted(_EXPECTED - seen)
    return TraceCoverageRecord(run_id=run_id, traceable_surfaces=sorted(seen), missing_surfaces=missing)
