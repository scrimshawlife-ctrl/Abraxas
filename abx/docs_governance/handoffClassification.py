from __future__ import annotations

from abx.docs_governance.handoffRecords import build_handoff_records


def classify_handoff_completeness() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "complete_handoff": [],
        "partial_handoff": [],
        "blocked_handoff": [],
        "stale_handoff": [],
        "not_computable": [],
    }
    for row in build_handoff_records():
        key = row.completeness if row.completeness in out else "not_computable"
        out[key].append(row.handoff_id)
    return {k: sorted(v) for k, v in out.items()}
