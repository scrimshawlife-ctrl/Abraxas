from __future__ import annotations

from abx.meta.types import AuthorityOfChangeRecord


def build_authority_of_change_records() -> list[AuthorityOfChangeRecord]:
    return [
        AuthorityOfChangeRecord(
            authority_id="auth-canon-priority-v3",
            change_id="chg-canon-priority-v3",
            approver_role="canonical-steward",
            review_chain=["reviewer-advisor", "delegated-steward"],
            escalation_path="governance-council",
        ),
        AuthorityOfChangeRecord(
            authority_id="auth-scorecard-thresholds-v2",
            change_id="chg-scorecard-thresholds-v2",
            approver_role="delegated-steward",
            review_chain=["reviewer-advisor"],
            escalation_path="canonical-steward",
        ),
        AuthorityOfChangeRecord(
            authority_id="auth-shadow-meta-lab",
            change_id="chg-shadow-meta-lab",
            approver_role="unknown",
            review_chain=[],
            escalation_path="not-defined",
        ),
    ]
