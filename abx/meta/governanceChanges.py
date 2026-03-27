from __future__ import annotations

from abx.meta.types import GovernanceChangeRecord


def build_governance_change_inventory() -> list[GovernanceChangeRecord]:
    return [
        GovernanceChangeRecord(
            change_id="chg-canon-priority-v3",
            title="canon precedence matrix refinement",
            change_class="precedence-changing",
            affected_domains=["governance", "decision"],
            state="approved-canonical-change",
            proposer="canon-steward",
        ),
        GovernanceChangeRecord(
            change_id="chg-scorecard-thresholds-v2",
            title="meta scorecard threshold normalization",
            change_class="implementation-aligned",
            affected_domains=["governance"],
            state="staged-candidate",
            proposer="meta-ops",
        ),
        GovernanceChangeRecord(
            change_id="chg-shadow-meta-lab",
            title="experimental stewardship ladder",
            change_class="canon-impacting",
            affected_domains=["governance", "documentation"],
            state="shadow-meta-experiment",
            proposer="research-steward",
        ),
    ]
