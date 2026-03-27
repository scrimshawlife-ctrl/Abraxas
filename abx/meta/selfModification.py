from __future__ import annotations

from abx.meta.types import SelfModificationRecord


def build_self_modification_records() -> list[SelfModificationRecord]:
    return [
        SelfModificationRecord(
            record_id="sm-canon-priority-v3",
            change_id="chg-canon-priority-v3",
            self_mod_kind="canon-precedence-rewrite",
            risk_level="medium",
            preconditions=["policy_review", "conflict_scan", "compatibility_pass"],
        ),
        SelfModificationRecord(
            record_id="sm-scorecard-thresholds-v2",
            change_id="chg-scorecard-thresholds-v2",
            self_mod_kind="governance-evaluator-tuning",
            risk_level="low",
            preconditions=["replay_check"],
        ),
        SelfModificationRecord(
            record_id="sm-shadow-meta-lab",
            change_id="chg-shadow-meta-lab",
            self_mod_kind="stewardship-model-experiment",
            risk_level="high",
            preconditions=["sandbox_containment", "explicit_shadow_label"],
        ),
    ]
