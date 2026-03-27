from __future__ import annotations

from abx.agency.types import DelegationRecord


def build_delegation_inventory() -> list[DelegationRecord]:
    rows = [
        DelegationRecord(
            delegation_id="delegation.operator.runtime",
            origin_actor="operator",
            delegate_actor="runtime_orchestrator",
            handoff_type="DIRECT_EXECUTION",
            inherited_scope="runtime.dispatch",
            max_depth=1,
        ),
        DelegationRecord(
            delegation_id="delegation.runtime.scheduler",
            origin_actor="runtime_orchestrator",
            delegate_actor="ers_scheduler",
            handoff_type="BOUNDED_DELEGATION",
            inherited_scope="scheduler.order",
            max_depth=2,
        ),
        DelegationRecord(
            delegation_id="delegation.scheduler.worker",
            origin_actor="ers_scheduler",
            delegate_actor="task_worker",
            handoff_type="ASSISTED_HANDOFF",
            inherited_scope="task.execute",
            max_depth=2,
        ),
        DelegationRecord(
            delegation_id="delegation.recovery.retry",
            origin_actor="resilience_supervisor",
            delegate_actor="recovery_drill",
            handoff_type="RETRY_REDELIVERY",
            inherited_scope="recovery.drill",
            max_depth=1,
        ),
        DelegationRecord(
            delegation_id="delegation.supervisor.escalation",
            origin_actor="resilience_supervisor",
            delegate_actor="operator",
            handoff_type="ESCALATION",
            inherited_scope="incident.escalation",
            max_depth=1,
        ),
    ]
    return sorted(rows, key=lambda x: x.delegation_id)
