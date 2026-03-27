from __future__ import annotations

from abx.meta.governanceChanges import build_governance_change_inventory


CHANGE_CLASSES = {
    "interpretation-only",
    "implementation-aligned",
    "canon-impacting",
    "precedence-changing",
    "lifecycle-changing",
    "identity-coherence-risk",
    "not-computable",
}


def classify_governance_changes() -> dict[str, list[str]]:
    buckets = {x.replace("-", "_"): [] for x in CHANGE_CLASSES}
    buckets.update(
        {
            "proposal": [],
            "staged_candidate": [],
            "approved_canonical_change": [],
            "shadow_meta_experiment": [],
            "superseded_change": [],
            "rejected_retired_change": [],
        }
    )
    for rec in build_governance_change_inventory():
        buckets.setdefault(rec.change_class.replace("-", "_"), []).append(rec.change_id)
        buckets.setdefault(rec.state.replace("-", "_"), []).append(rec.change_id)
    for ids in buckets.values():
        ids.sort()
    return buckets


def detect_hidden_meta_change() -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for rec in build_governance_change_inventory():
        if rec.change_class in {"precedence-changing", "canon-impacting"} and rec.state == "approved-canonical-change":
            continue
        if rec.change_class == "canon-impacting" and rec.state != "approved-canonical-change":
            issues.append({"changeId": rec.change_id, "reason": "canon_impact_not_approved"})
    return issues


def detect_change_taxonomy_drift() -> list[dict[str, str]]:
    drift: list[dict[str, str]] = []
    for rec in build_governance_change_inventory():
        if rec.change_class not in CHANGE_CLASSES:
            drift.append({"changeId": rec.change_id, "reason": "unknown_change_class", "changeClass": rec.change_class})
    return drift
