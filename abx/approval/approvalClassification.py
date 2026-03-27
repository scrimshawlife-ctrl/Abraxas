from __future__ import annotations


def classify_approval_state(*, approval_required: str, approver_id: str, raw_signal: str, valid_until: str, now: str = "2026-03-27T00:00:00Z") -> str:
    signal = raw_signal.strip().lower()
    if approval_required != "REQUIRED":
        return "NOT_COMPUTABLE"
    if not signal and not approver_id:
        return "APPROVAL_REQUIRED"
    if "denied" in signal:
        return "APPROVAL_DENIED"
    if valid_until < now:
        return "APPROVAL_EXPIRED"
    if any(x in signal for x in ("if", "condition", "rollback")):
        return "APPROVAL_CONDITIONAL"
    if signal in {"approved", "go ahead", "go-ahead"}:
        return "APPROVAL_GRANTED"
    if signal in {"requested", "pending"}:
        return "APPROVAL_REQUESTED"
    if signal in {"withdrawn", "revoked"}:
        return "APPROVAL_WITHDRAWN"
    if signal in {"acknowledged", "seen", "ok"}:
        return "BLOCKED_PENDING_APPROVAL"
    if not signal:
        return "APPROVAL_REQUESTED"
    return "INVALID_APPROVAL"
