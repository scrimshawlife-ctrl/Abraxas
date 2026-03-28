from __future__ import annotations

from abx.identity.types import ReferenceMismatchRecord


def build_identity_transition_records() -> tuple[ReferenceMismatchRecord, ...]:
    return (
        ReferenceMismatchRecord("trn.dup", "ref:acct-dup", "DUPLICATE_SUSPECTED", "similar-signature"),
        ReferenceMismatchRecord("trn.conf", "ref:acct-conflict", "DUPLICATE_CONFIRMED", "same-source-different-canon"),
        ReferenceMismatchRecord("trn.mismatch", "ref:crm-998", "REFERENCE_MISMATCH_ACTIVE", "federated-id-divergence"),
        ReferenceMismatchRecord("trn.dep", "ref:acct-legacy3", "DEPRECATED_IDENTIFIER_ACTIVE", "legacy-id-still-live"),
        ReferenceMismatchRecord("trn.remap", "ref:acct-remap", "REMAP_REQUIRED", "pre-merge-references"),
        ReferenceMismatchRecord("trn.done", "ref:acct-remap-complete", "CANONICAL_REFERENCE_RESTORED", "remap-propagated"),
    )
