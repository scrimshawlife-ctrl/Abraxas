from __future__ import annotations

from abx.semantic.types import SemanticDriftRecord


def build_semantic_inventory() -> tuple[SemanticDriftRecord, ...]:
    return (
        SemanticDriftRecord("sem.latency.unit", "packet.latency_ms", "UNIT", "MEANING_PRESERVED", "spec/v3:latency_ms"),
        SemanticDriftRecord("sem.risk.scale", "packet.risk_score", "INTERPRETIVE", "SEMANTIC_DRIFT_DETECTED", "audit/risk-scale-change"),
        SemanticDriftRecord("sem.alias.severity", "packet.severity", "LEXICAL", "SEMANTIC_ALIAS_ACTIVE", "schema/v4:severity_alias"),
        SemanticDriftRecord("sem.deprecated.confidence", "packet.confidence", "CATEGORICAL", "SEMANTIC_DEPRECATION_ACTIVE", "schema/v4:confidence_deprecated"),
        SemanticDriftRecord("sem.unknown.legacy", "packet.legacy_signal", "UNKNOWN", "NOT_COMPUTABLE", "migration/missing-map"),
    )
