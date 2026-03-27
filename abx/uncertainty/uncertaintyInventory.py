from __future__ import annotations

from abx.uncertainty.types import UncertaintyRecord


def build_uncertainty_inventory() -> tuple[UncertaintyRecord, ...]:
    return (
        UncertaintyRecord("unc.forecast.001", "FORECAST", "EPISTEMIC", "MODERATE", "NO"),
        UncertaintyRecord("unc.classifier.001", "CLASSIFICATION", "CALIBRATION", "HIGH", "YES"),
        UncertaintyRecord("unc.recommend.001", "RECOMMENDATION", "DATA_COVERAGE", "HIGH", "YES"),
        UncertaintyRecord("unc.ranking.001", "RANKING", "ALEATORIC", "LOW", "NO"),
        UncertaintyRecord("unc.anomaly.001", "ANOMALY_ALERT", "MIXED", "MODERATE", "YES"),
    )
