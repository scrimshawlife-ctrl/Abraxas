from __future__ import annotations

from abx.closure.types import RatificationCriteriaRecord


def build_ratification_criteria() -> list[RatificationCriteriaRecord]:
    rows = [
        RatificationCriteriaRecord(
            criteria_id="criteria.baseline_integrity",
            scope="baseline",
            required_domains=["domain.baseline", "domain.security", "domain.deployment"],
            requires_audit_ready=True,
            max_waived_domains=0,
        ),
        RatificationCriteriaRecord(
            criteria_id="criteria.operability_legibility",
            scope="governance-bundle",
            required_domains=["domain.docs", "domain.epistemic", "domain.meta"],
            requires_audit_ready=True,
            max_waived_domains=1,
        ),
        RatificationCriteriaRecord(
            criteria_id="criteria.external_consumption",
            scope="package",
            required_domains=["domain.product", "domain.performance"],
            requires_audit_ready=False,
            max_waived_domains=1,
        ),
    ]
    return sorted(rows, key=lambda x: x.criteria_id)
