from __future__ import annotations

from abx.approval.types import ConsentStateRecord


def build_consent_inventory() -> tuple[ConsentStateRecord, ...]:
    return (
        ConsentStateRecord("consent.001", "apr.deploy.001", "EXPLICIT_APPROVAL", "ticket:rel-100"),
        ConsentStateRecord("consent.002", "apr.override.001", "EXPIRED_CONSENT", "ticket:ovr-20"),
        ConsentStateRecord("consent.003", "apr.external.001", "CONDITIONAL_APPROVAL", "chat:ops-3"),
        ConsentStateRecord("consent.004", "apr.destroy.001", "DENIED_CONSENT", "ticket:sec-1"),
        ConsentStateRecord("consent.005", "apr.publish.001", "AMBIGUOUS_CONSENT", "comment:pub-9"),
        ConsentStateRecord("consent.006", "apr.connector.001", "ACKNOWLEDGMENT_ONLY", "note:int-7"),
        ConsentStateRecord("consent.007", "apr.connector.001", "WITHDRAWN_CONSENT", "chat:int-11"),
        ConsentStateRecord("consent.008", "apr.publish.001", "PREFERENCE_ONLY", "chat:comms-44"),
    )
