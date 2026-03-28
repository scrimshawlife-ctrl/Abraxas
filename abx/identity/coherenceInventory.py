from __future__ import annotations

from abx.identity.types import AliasRecord, MergeRecord, ReferentialCoherenceRecord, SplitRecord


def build_coherence_inventory() -> tuple[ReferentialCoherenceRecord, ...]:
    return (
        ReferentialCoherenceRecord("coh.base", "ent.account.001", "REFERENTIALLY_COHERENT", "DOWNSTREAM_ALIGNED"),
        ReferentialCoherenceRecord("coh.alias", "ent.account.002", "ALIAS_ACTIVE_COHERENT", "DOWNSTREAM_ALIGNED"),
        ReferentialCoherenceRecord("coh.merge", "ent.account.003", "MERGE_ACTIVE_COHERENT", "DOWNSTREAM_PARTIAL"),
        ReferentialCoherenceRecord("coh.split", "ent.account.004", "SPLIT_ACTIVE_COHERENT", "DOWNSTREAM_PARTIAL"),
        ReferentialCoherenceRecord("coh.dup", "ent.account.005", "DUPLICATE_ENTITY_SUSPECTED", "DOWNSTREAM_CONFLICT"),
        ReferentialCoherenceRecord("coh.bad", "ent.account.006", "DUPLICATE_ENTITY_CONFIRMED", "DOWNSTREAM_CONFLICT"),
    )


def build_alias_inventory() -> tuple[AliasRecord, ...]:
    return (
        AliasRecord("als.1", "ent.account.001", "acct-primary", "ALIAS_RESOLVED"),
        AliasRecord("als.2", "ent.account.003", "acct-legacy3", "DEPRECATED_IDENTIFIER_ACTIVE"),
    )


def build_merge_inventory() -> tuple[MergeRecord, ...]:
    return (
        MergeRecord("mrg.1", "ent.account.003a", "ent.account.003", "MERGE_ACTIVE"),
        MergeRecord("mrg.2", "ent.account.006a", "ent.account.006", "MERGE_ILLEGITIMATE"),
    )


def build_split_inventory() -> tuple[SplitRecord, ...]:
    return (
        SplitRecord("spl.1", "ent.account.004", "ent.account.004a", "SPLIT_ACTIVE"),
        SplitRecord("spl.2", "ent.account.005", "ent.account.005b", "SPLIT_ILLEGITIMATE"),
    )
