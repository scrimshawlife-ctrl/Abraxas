from __future__ import annotations

from abx.observability.types import CausalTraceSummary
from abx.trace.causalTrace import build_causal_trace
from abx.trace.traceCompression import compress_trace
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_trace_summary(*, run_id: str) -> CausalTraceSummary:
    trace = build_causal_trace(run_id=run_id)
    compressed = compress_trace(trace)
    degraded = [x.step for x in trace if x.state in {"DEGRADED", "REJECTED", "PARTIAL"}]
    payload = {"run_id": run_id, "compressed": compressed, "degraded": degraded}
    digest = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return CausalTraceSummary(
        artifact_id=f"causal-trace-summary-{run_id}",
        run_id=run_id,
        steps=compressed,
        degraded_points=degraded,
        summary_hash=digest,
    )
