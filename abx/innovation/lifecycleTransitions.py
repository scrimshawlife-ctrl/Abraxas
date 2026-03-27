from __future__ import annotations

from abx.innovation.innovationLifecycle import build_innovation_lifecycle_records


LIFECYCLE_STATES = {
    "sandboxed",
    "prototyped",
    "canary-evaluated",
    "promotion-ready",
    "promoted",
    "retired",
    "stalled",
    "not-computable",
}


def classify_lifecycle_states() -> dict[str, list[str]]:
    bucket: dict[str, list[str]] = {x.replace("-", "_"): [] for x in LIFECYCLE_STATES}
    for rec in build_innovation_lifecycle_records():
        bucket.setdefault(rec.state.replace("-", "_"), []).append(rec.experiment_id)
    for ids in bucket.values():
        ids.sort()
    return bucket


def detect_redundant_lifecycle_grammar() -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for rec in build_innovation_lifecycle_records():
        if rec.state not in LIFECYCLE_STATES:
            issues.append(
                {
                    "experimentId": rec.experiment_id,
                    "reason": "unknown_lifecycle_state",
                    "state": rec.state,
                }
            )
    return issues
