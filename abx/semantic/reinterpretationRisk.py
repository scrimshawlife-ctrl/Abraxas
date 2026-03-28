from __future__ import annotations

from abx.semantic.types import ReinterpretationRiskRecord


def build_reinterpretation_risk_records() -> tuple[ReinterpretationRiskRecord, ...]:
    return (
        ReinterpretationRiskRecord("rr.packet.latency", "packet.latency_ms", "LOW", "SAFE"),
        ReinterpretationRiskRecord("rr.risk.score", "packet.risk_score", "MEDIUM", "SAFE_WITH_MIGRATION"),
        ReinterpretationRiskRecord("rr.severity", "packet.severity", "HIGH", "TRANSLATION_REQUIRED"),
        ReinterpretationRiskRecord("rr.legacy", "packet.legacy_signal", "CRITICAL", "BLOCKED"),
    )
