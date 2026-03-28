from __future__ import annotations

from abx.identity.types import CanonicalReferenceRecord, EntityPersistenceRecord


def build_persistence_inventory() -> tuple[EntityPersistenceRecord, ...]:
    return (
        EntityPersistenceRecord("per.main", "ent.account.001", "PERSISTENT_CANONICAL_IDENTITY", "cont/account-001"),
        EntityPersistenceRecord("per.remap", "ent.account.002", "REMAPPED_CANONICAL_IDENTITY", "cont/account-002-remap"),
        EntityPersistenceRecord("per.dep", "ent.account.003", "DEPRECATED_IDENTIFIER", "cont/account-003"),
        EntityPersistenceRecord("per.display", "ent.account.004", "DISPLAY_ALIAS_ONLY", "cont/account-004"),
        EntityPersistenceRecord("per.shadow", "ent.account.005", "IMPORTED_IDENTITY_SHADOW", "cont/account-005"),
        EntityPersistenceRecord("per.break", "ent.account.006", "IDENTITY_BREAK", "unknown"),
    )


def build_canonical_reference_inventory() -> tuple[CanonicalReferenceRecord, ...]:
    return (
        CanonicalReferenceRecord("can.001", "ent.account.001", "CANONICAL_CLEAR", "registry/v1"),
        CanonicalReferenceRecord("can.002", "ent.account.002", "CANONICAL_REMAP_ACTIVE", "migration/v2"),
        CanonicalReferenceRecord("can.003", "ent.account.003", "CANONICAL_DEPRECATED", "deprecation/v1"),
        CanonicalReferenceRecord("can.004", "ent.account.004", "DISPLAY_ONLY", "ui-layer"),
    )
