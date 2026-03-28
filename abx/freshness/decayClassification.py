from __future__ import annotations


def classify_freshness(*, freshness_state: str, reuse_posture: str, decay_state: str) -> str:
    if freshness_state in {"BLOCKED", "NOT_COMPUTABLE", "DECAY_UNKNOWN"}:
        return freshness_state
    if reuse_posture == "REUSE_BLOCKED":
        if freshness_state in {"EXPIRED", "ARCHIVAL_ONLY"}:
            return freshness_state
        return "REUSE_BLOCKED"
    if freshness_state in {"FRESH", "FRESH_WITH_WARNING", "AGING", "STALE", "EXPIRED", "ARCHIVAL_ONLY", "REFRESH_REQUIRED"}:
        return freshness_state
    if decay_state == "DECAY_UNKNOWN":
        return "DECAY_UNKNOWN"
    return "AGING"
