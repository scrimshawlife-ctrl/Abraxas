from __future__ import annotations

from abx.agency.types import AutonomousOperationRecord


def build_autonomous_operation_inventory() -> list[AutonomousOperationRecord]:
    rows = [
        AutonomousOperationRecord(
            operation_id="auto.runtime_orchestrator.dispatch",
            surface_id="abx.runtime_orchestrator.execute_run_plan",
            mode="OPERATOR_CONFIRMED_ACTION",
            authority_scope="runtime.dispatch",
            stop_conditions=["missing_scheduler_metadata", "boundary_block"],
            status="GUARDRAILED",
        ),
        AutonomousOperationRecord(
            operation_id="auto.scheduler.partitioned",
            surface_id="abx.scheduler.scaleHandling.run_partitioned_scheduler",
            mode="DELEGATED_ACTION",
            authority_scope="scheduler.partition",
            stop_conditions=["task_metadata_invalid", "fanout_ceiling"],
            status="GUARDRAILED",
        ),
        AutonomousOperationRecord(
            operation_id="auto.review_scheduler",
            surface_id="abx.review_scheduler",
            mode="BOUNDED_AUTONOMOUS_ACTION",
            authority_scope="review.schedule",
            stop_conditions=["time_window_closed", "ledger_write_block"],
            status="DEGRADED",
        ),
        AutonomousOperationRecord(
            operation_id="auto.forecast_state",
            surface_id="abx.forecast_review_state",
            mode="RECOMMENDATION_ONLY",
            authority_scope="forecast.review.state",
            stop_conditions=["scheduler_ledger_missing"],
            status="ANALYSIS_ONLY",
        ),
        AutonomousOperationRecord(
            operation_id="auto.scorecard_reports",
            surface_id="scripts.run_*_scorecard",
            mode="ANALYSIS_ONLY",
            authority_scope="governance.reporting",
            stop_conditions=["artifact_build_failed"],
            status="ANALYSIS_ONLY",
        ),
    ]
    return sorted(rows, key=lambda x: x.operation_id)
