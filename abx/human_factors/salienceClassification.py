from __future__ import annotations

from abx.human_factors.prioritization import build_prioritization_records


SALIENCE = ("must_act_now", "should_review", "contextual", "background", "archival_reference")


def classify_salience() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in SALIENCE}
    for row in build_prioritization_records():
        out[row.salience].append(row.priority_id)
    return {k: sorted(v) for k, v in out.items()}


def classify_urgency() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"critical": [], "high": [], "medium": [], "low": []}
    for row in build_prioritization_records():
        out[row.urgency].append(row.priority_id)
    return {k: sorted(v) for k, v in out.items()}
