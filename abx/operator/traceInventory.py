from __future__ import annotations

from abx.operator.types import OperatorTraceRecord


def build_trace_inventory() -> tuple[OperatorTraceRecord, ...]:
    return (
        OperatorTraceRecord(
            trace_id="trc.corrective.cache-reset.001",
            intervention_id="int.corrective.cache-reset.001",
            actor_id="operator.incident",
            authority_ref="apr.override.001",
            reason_text="Cache corruption detected by checksum divergence",
            scope_ref="cache/reset/feed-shard-2",
            reversibility_signal="reversible",
            restoration_ticket="rst.feed-freeze.001",
            trace_state_signal="complete",
        ),
        OperatorTraceRecord(
            trace_id="trc.emergency.rule-hotfix.001",
            intervention_id="int.emergency.rule-hotfix.001",
            actor_id="operator.incident",
            authority_ref="apr.override.001",
            reason_text="",
            scope_ref="policy/filter/global",
            reversibility_signal="restoration-required",
            restoration_ticket="",
            trace_state_signal="partial",
        ),
        OperatorTraceRecord(
            trace_id="trc.bypass.direct-write.001",
            intervention_id="int.bypass.direct-write.001",
            actor_id="operator.admin",
            authority_ref="",
            reason_text="Speed run patch",
            scope_ref="identity/store/all-tenants",
            reversibility_signal="non-reversible",
            restoration_ticket="",
            trace_state_signal="partial",
        ),
    )
