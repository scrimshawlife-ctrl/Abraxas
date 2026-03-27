from __future__ import annotations

from abx.human_factors.types import OperatorPathRecord


def build_operator_paths() -> list[OperatorPathRecord]:
    return [
        OperatorPathRecord("path.normal.inspect", "normal", "operator.console.overview", "operator.console.scorecards", "canonical", "summary.overview.primary"),
        OperatorPathRecord("path.degraded.trace", "degraded", "operator.console.overview", "operator.console.trace_drilldown", "adapted", "summary.scorecard.secondary"),
        OperatorPathRecord("path.incident.contain", "incident", "operator.incident.runbook_view", "operator.console.trace_drilldown", "canonical", "action.contain.incident"),
        OperatorPathRecord("path.recovery.rollback", "recovery", "operator.incident.runbook_view", "operator.console.overview", "canonical", "action.rollback.incident"),
        OperatorPathRecord("path.legacy.mixed", "normal", "legacy.multi_entry_dashboard", "operator.console.overview", "legacy", "action.defer.legacy"),
    ]
