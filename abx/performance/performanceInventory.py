from __future__ import annotations

from abx.performance.types import PerformanceSurfaceRecord


def build_performance_surface_inventory() -> list[PerformanceSurfaceRecord]:
    return [
        PerformanceSurfaceRecord(
            surface_id="core.runtime_orchestrator.dispatch",
            workflow="run_execution",
            capability="scheduler_dispatch",
            environment_scope="all",
            criticality="critical_path",
            cost_class="core_runtime",
            owner="runtime",
        ),
        PerformanceSurfaceRecord(
            surface_id="core.execution_validator.validate",
            workflow="run_execution",
            capability="validation_proof_generation",
            environment_scope="all",
            criticality="critical_path",
            cost_class="core_runtime",
            owner="governance",
        ),
        PerformanceSurfaceRecord(
            surface_id="interop.federation.handoff",
            workflow="cross_system_handoff",
            capability="adapter_interop",
            environment_scope="networked",
            criticality="important_non_critical",
            cost_class="adapter_overhead",
            owner="federation",
        ),
        PerformanceSurfaceRecord(
            surface_id="observability.summary_assembly",
            workflow="operator_inspection",
            capability="report_generation",
            environment_scope="all",
            criticality="background_auxiliary",
            cost_class="observability_overhead",
            owner="observability",
        ),
        PerformanceSurfaceRecord(
            surface_id="governance.scorecard_bundle",
            workflow="governance_audits",
            capability="scorecard_serialization",
            environment_scope="all",
            criticality="background_auxiliary",
            cost_class="governance_overhead",
            owner="governance",
        ),
        PerformanceSurfaceRecord(
            surface_id="legacy.batch_backfill_14d",
            workflow="maintenance",
            capability="historical_backfill",
            environment_scope="batch",
            criticality="legacy_redundant_candidate",
            cost_class="optional_operator",
            owner="operations",
        ),
    ]
