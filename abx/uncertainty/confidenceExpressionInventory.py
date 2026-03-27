from __future__ import annotations

from abx.uncertainty.types import ConfidenceExpressionRecord


def build_confidence_expression_inventory() -> tuple[ConfidenceExpressionRecord, ...]:
    return (
        ConfidenceExpressionRecord("expr.forecast", "FORECAST", "INTERVAL", "0.42-0.57"),
        ConfidenceExpressionRecord("expr.classifier", "CLASSIFICATION", "CATEGORICAL", "MEDIUM"),
        ConfidenceExpressionRecord("expr.recommend", "RECOMMENDATION", "SUPPRESSED", ""),
        ConfidenceExpressionRecord("expr.ranking", "RANKING", "NUMERIC", "0.81"),
        ConfidenceExpressionRecord("expr.anomaly", "ANOMALY_ALERT", "QUALITATIVE", "tentative"),
    )
