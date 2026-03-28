from __future__ import annotations

from abx.explanation.types import CausalLanguageRecord, InterpretiveHonestyRecord, OmissionRiskRecord


def build_honesty_inventory() -> tuple[InterpretiveHonestyRecord, ...]:
    return (
        InterpretiveHonestyRecord("hon.ops", "operator.writeup", "INTERPRETIVELY_HONEST", "LOW"),
        InterpretiveHonestyRecord("hon.exec", "executive.summary", "INTERPRETIVELY_COMPRESSED_BUT_HONEST", "LOW"),
        InterpretiveHonestyRecord("hon.dash", "dashboard.card", "CAVEAT_OMISSION_RISK", "MEDIUM"),
        InterpretiveHonestyRecord("hon.causal", "causal.summary", "UNSUPPORTED_EXPLANATORY_JUMP", "HIGH"),
    )


def build_causal_inventory() -> tuple[CausalLanguageRecord, ...]:
    return (
        CausalLanguageRecord("csl.ops", "operator.writeup", "CAUSAL_LANGUAGE_ABSTAINED", "SUFFICIENT"),
        CausalLanguageRecord("csl.causal", "causal.summary", "CAUSAL_LANGUAGE_USED", "INSUFFICIENT"),
        CausalLanguageRecord("csl.forecast", "forecast.narrative", "CAUSAL_LANGUAGE_USED", "AMBIGUOUS"),
    )


def build_omission_inventory() -> tuple[OmissionRiskRecord, ...]:
    return (
        OmissionRiskRecord("om.ops", "operator.writeup", "OMISSION_CLEAR", "NO"),
        OmissionRiskRecord("om.exec", "executive.summary", "OMISSION_NOTED", "YES"),
        OmissionRiskRecord("om.card", "dashboard.card", "CAVEAT_OMISSION_RISK", "YES"),
        OmissionRiskRecord("om.legacy", "legacy.explanation", "NOT_COMPUTABLE", "UNKNOWN"),
    )
