from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OracleSignalItemV2:
    signal_id: str
    domain: str
    subdomain: str
    score: float
    confidence: float
    decay: float
    tier: str
    route: str

    def to_dict(self) -> dict:
        return {
            "schema_id": "OracleSignalItem.v2",
            "signal_id": self.signal_id,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "score": self.score,
            "confidence": self.confidence,
            "decay": self.decay,
            "tier": self.tier,
            "route": self.route,
            "authority_marker": "interpretation_only",
        }
