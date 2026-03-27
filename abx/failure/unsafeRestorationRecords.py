from __future__ import annotations

from abx.failure.types import UnsafeRestorationRecord


def build_unsafe_restoration_records() -> tuple[UnsafeRestorationRecord, ...]:
    return (
        UnsafeRestorationRecord("unsafe.cache", "err.cache.corrupt", "UNSAFE_RESTORATION", "integrity_uncleared"),
        UnsafeRestorationRecord("unsafe.db", "err.db.schema", "RESTORE_FORBIDDEN", "schema_unfixed"),
    )
