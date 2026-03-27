from __future__ import annotations

from abx.performance.types import OverheadAttributionRecord


def build_overhead_attribution() -> list[OverheadAttributionRecord]:
    return [
        OverheadAttributionRecord(
            record_id="ovh.observability.summary",
            surface_id="observability.summary_assembly",
            overhead_type="observability_overhead",
            ownership="observability",
            avoidability="partially_avoidable",
            accounting_mode="estimated_proxy",
        ),
        OverheadAttributionRecord(
            record_id="ovh.federation.handoff",
            surface_id="interop.federation.handoff",
            overhead_type="adapter_overhead",
            ownership="federation",
            avoidability="partially_avoidable",
            accounting_mode="heuristic",
        ),
        OverheadAttributionRecord(
            record_id="ovh.governance.scorecard",
            surface_id="governance.scorecard_bundle",
            overhead_type="governance_overhead",
            ownership="governance",
            avoidability="required",
            accounting_mode="accounted",
        ),
    ]


def classify_overhead_attribution() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "observability_overhead": [],
        "adapter_overhead": [],
        "governance_overhead": [],
    }
    for row in build_overhead_attribution():
        out[row.overhead_type].append(row.record_id)
    return {k: sorted(v) for k, v in out.items()}
