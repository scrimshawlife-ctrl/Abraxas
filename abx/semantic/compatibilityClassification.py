from __future__ import annotations


def classify_compatibility(*, structural_compatibility: str, semantic_compatibility: str) -> str:
    if "NOT_COMPUTABLE" in {structural_compatibility, semantic_compatibility}:
        return "NOT_COMPUTABLE"
    if semantic_compatibility == "SEMANTICALLY_COMPATIBLE":
        return "BACKWARD_COMPATIBLE"
    if semantic_compatibility == "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED":
        return "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED"
    if structural_compatibility == "ADAPTER_ONLY_COMPATIBLE":
        return "BACKWARD_PARSEABLE_ONLY"
    if semantic_compatibility == "MIGRATION_REQUIRED":
        return "MIGRATION_REQUIRED"
    return "SEMANTIC_BREAK"
