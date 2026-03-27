from __future__ import annotations

from abx.failure.types import ErrorTaxonomyRecord


def build_error_inventory() -> tuple[ErrorTaxonomyRecord, ...]:
    return (
        ErrorTaxonomyRecord("err.net.timeout", "connector", "external", "MEDIUM", "TRANSIENT_ERROR"),
        ErrorTaxonomyRecord("err.db.schema", "persistence", "internal", "HIGH", "PERSISTENT_ERROR"),
        ErrorTaxonomyRecord("err.cache.corrupt", "cache", "internal", "CRITICAL", "INTEGRITY_RISK_FAILURE"),
        ErrorTaxonomyRecord("err.dep.auth", "dependency", "external", "HIGH", "EXTERNAL_DEPENDENCY_FAILURE"),
        ErrorTaxonomyRecord("err.orch.invalid", "orchestration", "internal", "HIGH", "STATE_INVALIDITY"),
    )
