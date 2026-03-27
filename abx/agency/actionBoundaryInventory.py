from __future__ import annotations

from abx.agency.types import ActionBoundaryRecord


def build_action_boundary_inventory() -> list[ActionBoundaryRecord]:
    rows = [
        ActionBoundaryRecord(
            boundary_id="boundary.analysis.forecast_review",
            surface_id="abx.forecast_review_state",
            transition_class="ANALYSIS_TO_RECOMMENDATION",
            side_effect_capability="NO_SIDE_EFFECTS",
            governance_state="NO_SIDE_EFFECTS",
        ),
        ActionBoundaryRecord(
            boundary_id="boundary.runtime.scheduler_dispatch",
            surface_id="abx.runtime_orchestrator.execute_run_plan",
            transition_class="RECOMMENDATION_TO_ACTION",
            side_effect_capability="SIDE_EFFECT_CAPABLE",
            governance_state="SIDE_EFFECT_OBSERVED",
        ),
        ActionBoundaryRecord(
            boundary_id="boundary.scheduler.worker_dispatch",
            surface_id="abx.ers_scheduler.run_scheduler",
            transition_class="ACTION_CHAIN",
            side_effect_capability="SIDE_EFFECT_CAPABLE",
            governance_state="SIDE_EFFECT_OBSERVED",
        ),
        ActionBoundaryRecord(
            boundary_id="boundary.recovery.automation",
            surface_id="abx.resilience.recoveryDrills",
            transition_class="ACTION_CHAIN",
            side_effect_capability="SIDE_EFFECT_CAPABLE",
            governance_state="SIDE_EFFECT_BLOCKED",
        ),
        ActionBoundaryRecord(
            boundary_id="boundary.script.direct_entry",
            surface_id="scripts/run_runtime_orchestrator.py",
            transition_class="DIRECT_ENTRY_ACTION",
            side_effect_capability="SIDE_EFFECT_CAPABLE",
            governance_state="HIDDEN_CHANNEL_SUSPECTED",
        ),
    ]
    return sorted(rows, key=lambda x: x.boundary_id)
