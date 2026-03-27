from __future__ import annotations

from abx.human_factors.types import CognitiveLoadRecord


def build_cognitive_load_inventory() -> list[CognitiveLoadRecord]:
    return [
        CognitiveLoadRecord("load.overview.normal", "operator.console.overview", "bounded", 1, "low"),
        CognitiveLoadRecord("load.scorecards.normal", "operator.console.scorecards", "moderate", 2, "medium"),
        CognitiveLoadRecord("load.trace.degraded", "operator.console.trace_drilldown", "high", 4, "high"),
        CognitiveLoadRecord("load.legacy.dashboard", "legacy.multi_entry_dashboard", "overloaded", 5, "high"),
    ]
