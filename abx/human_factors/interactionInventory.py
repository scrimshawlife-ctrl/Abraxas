from __future__ import annotations

from abx.human_factors.types import InteractionSurfaceRecord


def build_interaction_inventory() -> list[InteractionSurfaceRecord]:
    return [
        InteractionSurfaceRecord(
            surface_id="operator.console.overview",
            task_type="inspect_system_state",
            workflow_phase="normal",
            condition_scope="normal",
            surface_class="primary",
            owner="operations",
            expertise_level="baseline",
        ),
        InteractionSurfaceRecord(
            surface_id="operator.console.scorecards",
            task_type="review_governance",
            workflow_phase="normal",
            condition_scope="normal",
            surface_class="secondary",
            owner="governance",
            expertise_level="baseline",
        ),
        InteractionSurfaceRecord(
            surface_id="operator.console.trace_drilldown",
            task_type="inspect_causality",
            workflow_phase="degraded",
            condition_scope="degraded",
            surface_class="drilldown",
            owner="observability",
            expertise_level="advanced",
        ),
        InteractionSurfaceRecord(
            surface_id="operator.incident.runbook_view",
            task_type="contain_incident",
            workflow_phase="incident",
            condition_scope="incident",
            surface_class="contextual_only",
            owner="operations",
            expertise_level="advanced",
        ),
        InteractionSurfaceRecord(
            surface_id="legacy.multi_entry_dashboard",
            task_type="mixed",
            workflow_phase="normal",
            condition_scope="normal",
            surface_class="legacy_deprecated_candidate",
            owner="integration",
            expertise_level="advanced",
        ),
    ]
