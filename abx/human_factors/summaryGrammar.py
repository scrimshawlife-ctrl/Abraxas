from __future__ import annotations

from abx.human_factors.types import SummarySurfaceRecord


def build_summary_surfaces() -> list[SummarySurfaceRecord]:
    return [
        SummarySurfaceRecord("summary.overview.primary", "overview", "overview_first", "operator.console.overview", "canonical"),
        SummarySurfaceRecord("summary.scorecard.secondary", "scorecard", "secondary", "operator.console.scorecards", "canonical"),
        SummarySurfaceRecord("summary.incident.context", "incident", "contextual", "operator.incident.runbook_view", "canonical"),
        SummarySurfaceRecord("summary.legacy.dashboard", "mixed", "flat", "legacy.multi_entry_dashboard", "redundant"),
    ]


def detect_redundant_summary_surfaces() -> list[str]:
    return sorted(x.summary_id for x in build_summary_surfaces() if x.redundancy_status == "redundant")
