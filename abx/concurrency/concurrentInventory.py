from __future__ import annotations

from abx.concurrency.types import ConcurrentOperationRecord


def build_concurrent_operation_inventory() -> list[ConcurrentOperationRecord]:
    rows = [
        ConcurrentOperationRecord(
            operation_id="op.scheduler.review_batch",
            actor_id="ers_scheduler",
            target_ref="forecast.review.window",
            domain_id="domain.review",
            action_class="WRITE",
            authority_scope="scheduler.order",
            side_effect_level="MEDIUM",
        ),
        ConcurrentOperationRecord(
            operation_id="op.runtime.plan_dispatch",
            actor_id="runtime_orchestrator",
            target_ref="runtime.execution.plan",
            domain_id="domain.runtime",
            action_class="WRITE",
            authority_scope="runtime.dispatch",
            side_effect_level="HIGH",
        ),
        ConcurrentOperationRecord(
            operation_id="op.recovery.rollback",
            actor_id="resilience_supervisor",
            target_ref="runtime.execution.plan",
            domain_id="domain.runtime",
            action_class="ROLLBACK",
            authority_scope="resilience.recover",
            side_effect_level="HIGH",
        ),
        ConcurrentOperationRecord(
            operation_id="op.notification.digest",
            actor_id="operator_notifier",
            target_ref="operator.digest.queue",
            domain_id="domain.notifications",
            action_class="NOTIFY",
            authority_scope="ops.notify",
            side_effect_level="LOW",
        ),
        ConcurrentOperationRecord(
            operation_id="op.scorecard.emit",
            actor_id="governance_reporter",
            target_ref="out.scorecards",
            domain_id="domain.governance",
            action_class="ANALYZE",
            authority_scope="governance.reporting",
            side_effect_level="NONE",
        ),
    ]
    return sorted(rows, key=lambda x: x.operation_id)
