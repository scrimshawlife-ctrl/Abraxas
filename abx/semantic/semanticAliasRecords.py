from __future__ import annotations

from abx.semantic.types import SemanticAliasRecord


def build_semantic_alias_records() -> tuple[SemanticAliasRecord, ...]:
    return (
        SemanticAliasRecord("alias.sev", "packet.severity_canonical", "packet.severity", "SEMANTIC_ALIAS_ACTIVE"),
        SemanticAliasRecord("alias.risk", "packet.risk_score", "packet.risk_index", "ALIAS_DRIFT_DETECTED"),
    )
