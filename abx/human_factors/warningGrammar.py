from __future__ import annotations

from abx.human_factors.types import WarningRecord


def build_warning_records() -> list[WarningRecord]:
    return [
        WarningRecord(
            warning_id="warn.integrity.mismatch",
            warning_class="integrity",
            salience="must_act_now",
            evidence_ref="integrity-audit#mismatches",
            next_action="verify",
            drilldown_surface="operator.console.trace_drilldown",
        ),
        WarningRecord(
            warning_id="warn.performance.drift",
            warning_class="performance",
            salience="should_review",
            evidence_ref="performance-surface-audit",
            next_action="inspect",
            drilldown_surface="operator.console.scorecards",
        ),
        WarningRecord(
            warning_id="warn.legacy.surface",
            warning_class="legacy",
            salience="contextual",
            evidence_ref="interaction-audit#legacy",
            next_action="defer",
            drilldown_surface="legacy.multi_entry_dashboard",
        ),
    ]


def detect_inconsistent_warning_vocabulary() -> list[str]:
    allowed = {"integrity", "performance", "security", "legacy", "continuity"}
    return sorted({x.warning_class for x in build_warning_records() if x.warning_class not in allowed})
