from __future__ import annotations

from abx.security.types import SecuritySurfaceRecord


def build_security_surface_inventory() -> list[SecuritySurfaceRecord]:
    return [
        SecuritySurfaceRecord(
            surface_id="boundary.input_envelope.validate",
            workflow="ingest",
            capability="input_validation",
            environment_scope="all",
            criticality="critical",
            security_domain="action_authorization",
            authority_class="authoritative",
            owner="boundary",
        ),
        SecuritySurfaceRecord(
            surface_id="deployment.secret_boundaries.enforce",
            workflow="deploy",
            capability="secret_boundary_enforcement",
            environment_scope="all",
            criticality="critical",
            security_domain="secret_credential_boundary",
            authority_class="authoritative",
            owner="deployment",
        ),
        SecuritySurfaceRecord(
            surface_id="governance.override_precedence.evaluate",
            workflow="decision_override",
            capability="override_containment",
            environment_scope="all",
            criticality="important_bounded",
            security_domain="abuse_control",
            authority_class="authoritative",
            owner="governance",
        ),
        SecuritySurfaceRecord(
            surface_id="federation.handoff_envelopes.verify",
            workflow="cross_system_handoff",
            capability="interop_contract_validation",
            environment_scope="networked",
            criticality="important_bounded",
            security_domain="integrity_verification",
            authority_class="derived",
            owner="federation",
        ),
        SecuritySurfaceRecord(
            surface_id="operations.incident_recovery.execute",
            workflow="incident_recovery",
            capability="containment_recovery",
            environment_scope="all",
            criticality="auxiliary",
            security_domain="operator_recovery",
            authority_class="authoritative",
            owner="operations",
        ),
        SecuritySurfaceRecord(
            surface_id="legacy.import_bridge.direct_adapter",
            workflow="import_export",
            capability="legacy_adapter_bridge",
            environment_scope="networked",
            criticality="legacy_redundant_candidate",
            security_domain="abuse_control",
            authority_class="legacy",
            owner="integration",
        ),
    ]
