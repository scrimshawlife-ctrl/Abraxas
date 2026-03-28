from __future__ import annotations

from abx.identity.types import IdentityResolutionRecord


def build_identity_inventory() -> tuple[IdentityResolutionRecord, ...]:
    return (
        IdentityResolutionRecord("idr.canon", "ref:acct-001", "CANONICAL_IDENTITY_RESOLVED", "ent.account.001"),
        IdentityResolutionRecord("idr.alias", "ref:acct-primary", "ALIAS_RESOLVED", "ent.account.001"),
        IdentityResolutionRecord("idr.foreign", "ref:crm-998", "FOREIGN_REFERENCE_RESOLVED", "ent.account.002"),
        IdentityResolutionRecord("idr.transient", "ref:session-42", "TRANSIENT_HANDLE_RESOLVED", "ent.session.042"),
        IdentityResolutionRecord("idr.amb", "ref:acct-dup", "REFERENCE_AMBIGUOUS", "unknown"),
        IdentityResolutionRecord("idr.unresolved", "ref:legacy-404", "UNRESOLVED_REFERENCE", "unknown"),
    )
