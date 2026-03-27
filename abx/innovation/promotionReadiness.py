from __future__ import annotations

from abx.innovation.innovationLifecycle import build_innovation_lifecycle_records
from abx.innovation.types import PromotionReadinessRecord


def build_promotion_readiness_records() -> list[PromotionReadinessRecord]:
    requirements = {
        "exp-hypothesis-routing-v2": ["policy_validation", "security_review", "replay_evidence"],
        "exp-latency-compression-3": ["performance_evidence", "security_review", "canary_report"],
        "exp-symbolic-memory-bridge": ["continuity_evidence", "boundary_review"],
        "exp-legacy-shadow-parser": ["owner_assignment", "boundary_containment"],
    }
    evidence = {
        "exp-hypothesis-routing-v2": ["policy_validation", "security_review", "replay_evidence"],
        "exp-latency-compression-3": ["performance_evidence", "canary_report"],
        "exp-symbolic-memory-bridge": ["boundary_review"],
        "exp-legacy-shadow-parser": [],
    }
    rows: list[PromotionReadinessRecord] = []
    for life in build_innovation_lifecycle_records():
        required = requirements[life.experiment_id]
        available = set(evidence[life.experiment_id])
        missing = sorted(x for x in required if x not in available)
        state = "ready" if not missing and life.state == "promotion-ready" else "blocked"
        rows.append(
            PromotionReadinessRecord(
                readiness_id=f"ready-{life.experiment_id}",
                experiment_id=life.experiment_id,
                readiness_state=state,
                required_evidence=required,
                missing_evidence=missing,
            )
        )
    return rows
