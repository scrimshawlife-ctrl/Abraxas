from __future__ import annotations

from abx.operator.types import ReversibilityRecord


def build_restoration_records() -> tuple[ReversibilityRecord, ...]:
    return (
        ReversibilityRecord(
            reversibility_id="rst.feed-freeze.001",
            intervention_id="int.corrective.cache-reset.001",
            reversibility_state="REVERSIBLE",
            restoration_required="NO",
        ),
        ReversibilityRecord(
            reversibility_id="rst.rule-hotfix.001",
            intervention_id="int.emergency.rule-hotfix.001",
            reversibility_state="REVERSIBLE",
            restoration_required="YES",
        ),
        ReversibilityRecord(
            reversibility_id="rst.identity-disable.001",
            intervention_id="int.prohibited.policy-disable.001",
            reversibility_state="NON_REVERSIBLE",
            restoration_required="YES",
        ),
    )
