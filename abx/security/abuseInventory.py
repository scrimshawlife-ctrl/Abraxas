from __future__ import annotations

from abx.security.types import AbuseContainmentRecord, AbusePathRecord


def build_abuse_path_inventory() -> list[AbusePathRecord]:
    return [
        AbusePathRecord(
            abuse_id="abuse.override_escalation",
            abuse_class="override_abuse",
            entry_surface="governance.override_inventory",
            target_surface="governance.override_precedence.evaluate",
            exposure_state="contained",
            owner="governance",
        ),
        AbusePathRecord(
            abuse_id="abuse.connector_semantic_drift",
            abuse_class="connector_adapter_abuse",
            entry_surface="federation.handoff_envelopes.verify",
            target_surface="decision.decision_records",
            exposure_state="monitored",
            owner="federation",
        ),
        AbusePathRecord(
            abuse_id="abuse.config_shadow_override",
            abuse_class="config_abuse",
            entry_surface="deployment.override_containment",
            target_surface="deployment.runtime_topology",
            exposure_state="contained",
            owner="deployment",
        ),
        AbusePathRecord(
            abuse_id="abuse.report_flood",
            abuse_class="report_observability_abuse",
            entry_surface="observability.summary_assembly",
            target_surface="operations.operator_console",
            exposure_state="contained",
            owner="observability",
        ),
        AbusePathRecord(
            abuse_id="abuse.legacy_import_bypass",
            abuse_class="interface_abuse",
            entry_surface="legacy.import_bridge.direct_adapter",
            target_surface="boundary.input_envelope.validate",
            exposure_state="legacy_exposure",
            owner="integration",
        ),
    ]


def build_abuse_containment_inventory() -> list[AbuseContainmentRecord]:
    return [
        AbuseContainmentRecord(
            containment_id="contain.override_precedence_gate",
            abuse_id="abuse.override_escalation",
            control_surface="governance.override_precedence.evaluate",
            control_mode="preventive_gate",
            status="contained",
            recovery_path="incident_override_rollback",
        ),
        AbuseContainmentRecord(
            containment_id="contain.handoff_contract_monitor",
            abuse_id="abuse.connector_semantic_drift",
            control_surface="federation.contract_compatibility",
            control_mode="detective_monitor",
            status="monitored",
            recovery_path="contract_downgrade_path",
        ),
        AbuseContainmentRecord(
            containment_id="contain.config_override_guard",
            abuse_id="abuse.config_shadow_override",
            control_surface="deployment.override_containment",
            control_mode="preventive_gate",
            status="contained",
            recovery_path="environment_reconcile",
        ),
        AbuseContainmentRecord(
            containment_id="contain.operator_report_budget",
            abuse_id="abuse.report_flood",
            control_surface="performance.budget.operator_report_bytes",
            control_mode="degradation_control",
            status="contained",
            recovery_path="truncate_optional_reports",
        ),
        AbuseContainmentRecord(
            containment_id="contain.legacy_bridge_review",
            abuse_id="abuse.legacy_import_bypass",
            control_surface="legacy.import_bridge.direct_adapter",
            control_mode="manual_review",
            status="partial",
            recovery_path="migrate_to_boundary_envelope",
        ),
    ]
