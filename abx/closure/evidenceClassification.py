from __future__ import annotations


def classify_bundle_state(*, missing_required_domains: list[str], stale_evidence_refs: list[str], blocked_domains: list[str]) -> str:
    if missing_required_domains:
        return "EVIDENCE_INCOMPLETE"
    if blocked_domains:
        return "BLOCKED"
    if stale_evidence_refs:
        return "STALE_EVIDENCE"
    return "AUDIT_READY"


def classify_audit_readiness(bundle_states: dict[str, str]) -> str:
    if not bundle_states:
        return "NOT_COMPUTABLE"
    values = set(bundle_states.values())
    if "BLOCKED" in values:
        return "BLOCKED"
    if "EVIDENCE_INCOMPLETE" in values:
        return "EVIDENCE_INCOMPLETE"
    if "STALE_EVIDENCE" in values:
        return "AUDIT_READY_WITH_GAPS"
    if values == {"AUDIT_READY"}:
        return "AUDIT_READY"
    return "NOT_COMPUTABLE"
