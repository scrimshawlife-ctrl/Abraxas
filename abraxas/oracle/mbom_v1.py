"""MBOM v1 — additive ambiguity-preservation layer.

This module is intentionally non-authoritative. It derives advisory ambiguity
signals from compression/forecast data without mutating routing decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class MBOMAssessment:
    subsystem_id: str
    lane: str
    authority: str
    ambiguity_score: float
    ambiguity_band: str
    blocked_change_classes: tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "lane": self.lane,
            "authority": self.authority,
            "ambiguity_score": self.ambiguity_score,
            "ambiguity_band": self.ambiguity_band,
            "blocked_change_classes": list(self.blocked_change_classes),
        }


def _band(score: float) -> str:
    if score < 0.34:
        return "LOW"
    if score < 0.67:
        return "MEDIUM"
    return "HIGH"


def assess_ambiguity(
    *,
    lifecycle_states: Dict[str, str],
    domain_signals: list[str],
    resonance_score: float,
) -> MBOMAssessment:
    """Compute deterministic MBOM ambiguity advisory.

    Score is bounded [0,1] and only used for observability/advisory output.
    """
    total_tokens = max(len(lifecycle_states), 1)
    unstable = sum(1 for v in lifecycle_states.values() if v in {"DRIFT", "SEED", "EMERGENT"})
    signal_factor = min(len(domain_signals) / 8.0, 1.0)
    resonance_factor = min(max(resonance_score, 0.0), 1.0)
    score = min(max((unstable / total_tokens) * 0.55 + signal_factor * 0.25 + resonance_factor * 0.20, 0.0), 1.0)

    return MBOMAssessment(
        subsystem_id="mbom_v1",
        lane="support",
        authority="non-authoritative",
        ambiguity_score=round(score, 6),
        ambiguity_band=_band(score),
        blocked_change_classes=("forecast_active_change", "authority_surface_drift"),
    )
