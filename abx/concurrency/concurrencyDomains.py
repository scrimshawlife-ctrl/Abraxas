from __future__ import annotations

from abx.concurrency.types import ConcurrencyDomainRecord


def build_concurrency_domains() -> list[ConcurrencyDomainRecord]:
    rows = [
        ConcurrencyDomainRecord("domain.runtime", "SERIALIZE_REQUIRED", "runtime", ["runtime.execution.plan", "runtime.events"]),
        ConcurrencyDomainRecord("domain.review", "MERGEABLE", "forecast", ["forecast.review.window"]),
        ConcurrencyDomainRecord("domain.notifications", "NON_CONFLICTING_OVERLAP", "operations", ["operator.digest.queue"]),
        ConcurrencyDomainRecord("domain.governance", "INDEPENDENT_CONCURRENT", "governance", ["out.scorecards"]),
    ]
    return sorted(rows, key=lambda x: x.domain_id)
