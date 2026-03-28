from __future__ import annotations

from abx.identity.types import AliasRecord


def build_deprecated_identifier_records() -> tuple[AliasRecord, ...]:
    return (
        AliasRecord("dep.1", "ent.account.003", "acct-legacy3", "DEPRECATED_IDENTIFIER_ACTIVE"),
        AliasRecord("dep.2", "ent.account.005", "acct-old-shadow", "DEPRECATED_IDENTIFIER_ACTIVE"),
    )
