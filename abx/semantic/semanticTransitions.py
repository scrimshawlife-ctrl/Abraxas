from __future__ import annotations

from abx.semantic.types import SemanticTransitionRecord


def build_semantic_transition_records() -> tuple[SemanticTransitionRecord, ...]:
    return (
        SemanticTransitionRecord(
            "st.risk.shift",
            "packet.risk_score",
            "SEMANTICALLY_COMPATIBLE",
            "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED",
            "risk_weight_reinterpretation",
            "DOWNGRADED",
        ),
        SemanticTransitionRecord(
            "st.alias.drift",
            "packet.severity",
            "SEMANTIC_ALIAS_ACTIVE",
            "ALIAS_DRIFT_DETECTED",
            "alias_diverged_from_canonical",
            "DOWNGRADED",
        ),
        SemanticTransitionRecord(
            "st.legacy.blocked",
            "packet.legacy_signal",
            "REINTERPRETATION_RISK",
            "BLOCKED",
            "unsafe_legacy_interpretation",
            "BLOCKED",
        ),
        SemanticTransitionRecord(
            "st.migration.restore",
            "packet.risk_score",
            "MIGRATION_REQUIRED",
            "MEANING_RESTORED",
            "migration_completed_and_validated",
            "RESTORED",
        ),
    )
