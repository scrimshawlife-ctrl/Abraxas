from __future__ import annotations


def classify_meaning_preservation(*, preservation_state: str, migration_state: str, translation_required: str) -> str:
    if preservation_state == "UNSAFE_REINTERPRETATION" or migration_state == "MIGRATION_ILLEGITIMATE":
        return "SEMANTIC_BREAK"
    if translation_required == "YES" and migration_state == "MIGRATION_INCOMPLETE":
        return "MIGRATION_REQUIRED"
    if preservation_state == "MEANING_PRESERVED_VIA_MIGRATION" and migration_state == "MIGRATION_COMPLETE":
        return "MEANING_PRESERVED"
    if preservation_state == "MEANING_PRESERVED":
        return "MEANING_PRESERVED"
    return "REINTERPRETATION_RISK"
