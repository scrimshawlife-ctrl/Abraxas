from __future__ import annotations

from abx.approval.types import ApproverValidityRecord, AuthorityToProceedRecord


ROLE_SCOPE = {
    "RELEASE_STEWARD": {"env/prod/release/2026.03.1", "connector/ledger/write", "connector/ledger/read"},
    "RISK_STEWARD": {"override/policy/risk-threshold"},
    "DELEGATE": {"commitment/ext/partner-a"},
}


def classify_authority(row: AuthorityToProceedRecord, now: str = "2026-03-27T00:00:00Z") -> str:
    if row.valid_until < now:
        return "EXPIRED_AUTHORITY"
    if row.actor_role == "DELEGATE":
        return "DELEGATED_AUTHORITY"
    if row.approved_scope != row.attempted_scope:
        return "SCOPE_INVALID_AUTHORITY"
    allowed = ROLE_SCOPE.get(row.actor_role)
    if not allowed:
        return "INVALID_AUTHORITY"
    if row.attempted_scope not in allowed:
        return "INVALID_AUTHORITY"
    return "VALID_AUTHORITY"


def build_approver_validity_records(records: tuple[AuthorityToProceedRecord, ...]) -> tuple[ApproverValidityRecord, ...]:
    return tuple(
        ApproverValidityRecord(
            validity_id=f"validity.{row.authority_id}",
            authority_id=row.authority_id,
            validity_state=classify_authority(row),
            reason="role_scope_time_binding",
        )
        for row in records
    )
