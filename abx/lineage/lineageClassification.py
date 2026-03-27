from __future__ import annotations


def classify_lineage(*, lineage_kind: str, source_ref: str) -> str:
    allowed = {"PRIMARY", "DERIVED", "MERGED", "COPIED", "CACHED", "MATERIALIZED"}
    if lineage_kind not in allowed:
        return "NOT_COMPUTABLE"
    if not source_ref:
        return "PROVENANCE_BROKEN"
    if lineage_kind == "PRIMARY":
        return "SOURCE_TRACEABLE_STATE"
    if lineage_kind == "DERIVED":
        return "DERIVED_WITH_VALID_LINEAGE"
    return f"{lineage_kind}_LINEAGE_STATE"
