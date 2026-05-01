from __future__ import annotations

from dataclasses import dataclass

THRESHOLDS = {
    "min_scores_used": 3,
    "min_improvement_delta": -0.01,
    "max_worsening_delta": 0.01,
}

AUTHORITY_FLAGS = {
    "review_recommendation": True,
    "overlay_activation": False,
    "baseline_mutation": False,
    "runtime_config_write": False,
    "promotion": False,
    "execution": False,
    "scheduler": False,
}


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    overlay_id: str
    entry_id: str | None
    proposal_id: str | None
    source_key: str
    status: str
    basis: dict
    reason: str
    lineage: dict

    def to_dict(self) -> dict:
        return {
            "recommendation_version": "CanaryReviewRecommendation.v1",
            "recommendation_id": self.recommendation_id,
            "overlay_id": self.overlay_id,
            "entry_id": self.entry_id,
            "proposal_id": self.proposal_id,
            "source_key": self.source_key,
            "status": self.status,
            "basis": self.basis,
            "thresholds": dict(THRESHOLDS),
            "reason": self.reason,
            "lineage": self.lineage,
            "authority": dict(AUTHORITY_FLAGS),
        }
