from __future__ import annotations

from abx.lineage.types import UnauthorizedMutationRecord


def build_unauthorized_mutation_records() -> tuple[UnauthorizedMutationRecord, ...]:
    return (
        UnauthorizedMutationRecord(
            "unauth.partner",
            "state.partner.merged",
            "UNAUTHORIZED_MUTATION",
            "QUARANTINE_ACTIVE",
            authority_ref="policy/federation-write@v1",
            quarantine_required="YES",
        ),
    )
