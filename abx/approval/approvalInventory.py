from __future__ import annotations

from abx.approval.types import HumanApprovalRecord


def build_approval_inventory() -> tuple[HumanApprovalRecord, ...]:
    return (
        HumanApprovalRecord(
            approval_id="apr.deploy.001",
            action_class="DEPLOYMENT_RELEASE",
            scope_ref="env/prod/release/2026.03.1",
            approval_required="REQUIRED",
            requested_by="operator.release",
            approver_id="steward.ops",
            requested_at="2026-03-20T09:00:00Z",
            valid_until="2026-03-30T09:00:00Z",
            raw_signal="approved",
        ),
        HumanApprovalRecord(
            approval_id="apr.override.001",
            action_class="OVERRIDE_EXECUTION",
            scope_ref="override/policy/risk-threshold",
            approval_required="REQUIRED",
            requested_by="operator.runtime",
            approver_id="steward.risk",
            requested_at="2026-03-10T09:00:00Z",
            valid_until="2026-03-18T09:00:00Z",
            raw_signal="approved",
        ),
        HumanApprovalRecord(
            approval_id="apr.external.001",
            action_class="EXTERNAL_COMMITMENT_CHANGE",
            scope_ref="commitment/ext/partner-a",
            approval_required="REQUIRED",
            requested_by="operator.commitment",
            approver_id="steward.commercial",
            requested_at="2026-03-26T12:00:00Z",
            valid_until="2026-04-01T00:00:00Z",
            raw_signal="please proceed if rollback is prepared",
        ),
        HumanApprovalRecord(
            approval_id="apr.destroy.001",
            action_class="DESTRUCTIVE_OPERATION",
            scope_ref="data/archive/segment-7",
            approval_required="REQUIRED",
            requested_by="operator.storage",
            approver_id="steward.security",
            requested_at="2026-03-27T00:00:00Z",
            valid_until="2026-03-28T00:00:00Z",
            raw_signal="denied",
        ),
        HumanApprovalRecord(
            approval_id="apr.publish.001",
            action_class="PUBLICATION_RELEASE",
            scope_ref="public/forecast/v21",
            approval_required="REQUIRED",
            requested_by="operator.comms",
            approver_id="",
            requested_at="2026-03-27T08:00:00Z",
            valid_until="2026-03-29T00:00:00Z",
            raw_signal="",
        ),
        HumanApprovalRecord(
            approval_id="apr.connector.001",
            action_class="PRIVILEGED_CONNECTOR_EXECUTION",
            scope_ref="connector/ledger/write",
            approval_required="REQUIRED",
            requested_by="operator.integrations",
            approver_id="steward.ops",
            requested_at="2026-03-27T05:00:00Z",
            valid_until="2026-03-29T00:00:00Z",
            raw_signal="acknowledged",
        ),
    )
