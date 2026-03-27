from __future__ import annotations

from abx.decision.decisionRecords import build_decision_records
from abx.governance.decision_types import DecisionCoverageRecord


def build_decision_coverage(run_id: str = "RUN-DECISION") -> list[DecisionCoverageRecord]:
    rows = []
    for row in build_decision_records(run_id=run_id):
        coverage = "COVERED" if row.policy_refs and row.value_refs and row.evidence_refs else "PARTIAL"
        rows.append(DecisionCoverageRecord(decision_id=row.decision_id, coverage=coverage))
    return sorted(rows, key=lambda x: x.decision_id)
