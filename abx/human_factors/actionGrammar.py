from __future__ import annotations

from abx.human_factors.types import ActionSurfaceRecord


def build_action_surfaces() -> list[ActionSurfaceRecord]:
    return [
        ActionSurfaceRecord("action.inspect.scorecard", "inspect", "operator.console.scorecards", "perm.operator.inspect", True),
        ActionSurfaceRecord("action.verify.integrity", "verify", "operator.console.trace_drilldown", "perm.governance.override", False),
        ActionSurfaceRecord("action.contain.incident", "contain", "operator.incident.runbook_view", "perm.incident.containment", False),
        ActionSurfaceRecord("action.rollback.incident", "rollback", "operator.incident.runbook_view", "perm.incident.containment", False),
        ActionSurfaceRecord("action.defer.legacy", "defer", "legacy.multi_entry_dashboard", "perm.operator.inspect", True),
    ]


def detect_action_grammar_drift() -> list[str]:
    allowed = {"inspect", "verify", "contain", "continue", "escalate", "rollback", "defer"}
    return sorted({x.action_class for x in build_action_surfaces() if x.action_class not in allowed})
