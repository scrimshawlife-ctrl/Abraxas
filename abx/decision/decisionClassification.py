from __future__ import annotations

from abx.decision.decisionRecords import build_decision_records


def classify_decision_completeness(run_id: str = "RUN-DECISION") -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in build_decision_records(run_id=run_id):
        grouped.setdefault(row.outcome.completeness, []).append(row.decision_id)
    return {k: sorted(v) for k, v in sorted(grouped.items())}
