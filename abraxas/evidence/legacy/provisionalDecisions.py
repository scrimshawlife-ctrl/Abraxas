from __future__ import annotations

from abx.evidence.types import ProvisionalDecisionRecord, UnmetBurdenRecord


def build_provisional_decision_records() -> tuple[ProvisionalDecisionRecord, ...]:
    return (
        ProvisionalDecisionRecord("prov.release.001", "RELEASE_DECISION", "PROVISIONAL_DECISION_ACTIVE", "2026-03-30T00:00:00Z"),
        ProvisionalDecisionRecord("prov.publish.001", "PUBLICATION_DECISION", "PROVISIONAL_DECISION_EXPIRED", "2026-03-20T00:00:00Z"),
    )


def build_unmet_burden_records() -> tuple[UnmetBurdenRecord, ...]:
    return (
        UnmetBurdenRecord("unmet.override.001", "POLICY_EXCEPTION", "BURDEN_UNMET", "insufficient counterfactual evidence"),
    )
