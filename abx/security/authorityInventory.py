from __future__ import annotations

from abx.security.types import ActionPermissionRecord, AuthorityBoundaryRecord


def build_authority_inventory() -> list[AuthorityBoundaryRecord]:
    return [
        AuthorityBoundaryRecord(
            boundary_id="auth.operator.inspect",
            actor="operator",
            action_class="inspect_report",
            scope="read_only",
            authority_status="authorized",
            owner="operations",
        ),
        AuthorityBoundaryRecord(
            boundary_id="auth.runtime.mutate_local",
            actor="runtime",
            action_class="mutate_local_state",
            scope="local",
            authority_status="authorized",
            owner="runtime",
        ),
        AuthorityBoundaryRecord(
            boundary_id="auth.governance.override",
            actor="governance_service",
            action_class="promote_release_override",
            scope="governed_state",
            authority_status="waiver_backed",
            owner="governance",
        ),
        AuthorityBoundaryRecord(
            boundary_id="auth.incident.emergency_contain",
            actor="incident_commander",
            action_class="containment_rollback_incident",
            scope="governed_state",
            authority_status="emergency_only",
            owner="operations",
        ),
        AuthorityBoundaryRecord(
            boundary_id="auth.adapter.direct_write",
            actor="legacy_adapter",
            action_class="mutate_governed_state",
            scope="governed_state",
            authority_status="prohibited",
            owner="integration",
        ),
    ]


def build_action_permissions() -> list[ActionPermissionRecord]:
    return [
        ActionPermissionRecord(
            permission_id="perm.operator.inspect",
            action_surface="operations.operator_console",
            action_class="inspect_report",
            authorization="authorized",
            condition="run_scope_assigned",
            precedence=10,
        ),
        ActionPermissionRecord(
            permission_id="perm.runtime.local_mutation",
            action_surface="runtime_orchestrator",
            action_class="mutate_local_state",
            authorization="authorized_under_condition",
            condition="boundary_validation_passed",
            precedence=20,
        ),
        ActionPermissionRecord(
            permission_id="perm.governance.override",
            action_surface="governance.override_precedence.evaluate",
            action_class="promote_release_override",
            authorization="waiver_backed",
            condition="approved_waiver_present",
            precedence=30,
        ),
        ActionPermissionRecord(
            permission_id="perm.incident.containment",
            action_surface="operations.incidents",
            action_class="containment_rollback_incident",
            authorization="emergency_only",
            condition="incident_declared",
            precedence=40,
        ),
        ActionPermissionRecord(
            permission_id="perm.adapter.write",
            action_surface="legacy.import_bridge.direct_adapter",
            action_class="mutate_governed_state",
            authorization="prohibited",
            condition="always_denied",
            precedence=50,
        ),
    ]
