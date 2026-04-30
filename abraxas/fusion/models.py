from __future__ import annotations

from dataclasses import dataclass

ALLOWED_DOMAINS = {"oracle", "market_pse", "social_level99", "code_governance", "operator", "unknown"}
ALLOWED_POLARITY = {"positive", "negative", "neutral", "unknown"}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class CrossDomainSignal:
    schema_version: str
    signal_id: str
    domain: str
    polarity: str
    magnitude: float
    confidence: float
    freshness: float

    @classmethod
    def from_dict(cls, payload: dict) -> "CrossDomainSignal":
        domain = payload.get("domain", "unknown")
        polarity = payload.get("polarity", "unknown")
        if domain not in ALLOWED_DOMAINS or polarity not in ALLOWED_POLARITY:
            raise ValueError("NOT_COMPUTABLE")
        return cls(
            schema_version=str(payload.get("schema_version", "CrossDomainSignal.v1")),
            signal_id=str(payload.get("signal_id", "")),
            domain=domain,
            polarity=polarity,
            magnitude=clamp01(payload.get("magnitude", 0.0)),
            confidence=clamp01(payload.get("confidence", 0.0)),
            freshness=clamp01(payload.get("freshness", 0.0)),
        )
