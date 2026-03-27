from __future__ import annotations

from abx.approval.types import AuthorityToProceedRecord


def build_authority_inventory() -> tuple[AuthorityToProceedRecord, ...]:
    return (
        AuthorityToProceedRecord("auth.001", "apr.deploy.001", "steward.ops", "RELEASE_STEWARD", "env/prod/release/2026.03.1", "env/prod/release/2026.03.1", "2026-03-30T09:00:00Z"),
        AuthorityToProceedRecord("auth.002", "apr.override.001", "steward.risk", "RISK_STEWARD", "override/policy/risk-threshold", "override/policy/risk-threshold", "2026-03-18T09:00:00Z"),
        AuthorityToProceedRecord("auth.003", "apr.external.001", "delegate.commercial", "DELEGATE", "commitment/ext/partner-a", "commitment/ext/partner-a", "2026-03-29T00:00:00Z"),
        AuthorityToProceedRecord("auth.004", "apr.publish.001", "observer.comms", "VIEWER", "public/forecast/v21", "public/forecast/v21", "2026-04-05T00:00:00Z"),
        AuthorityToProceedRecord("auth.005", "apr.connector.001", "steward.ops", "RELEASE_STEWARD", "connector/ledger/read", "connector/ledger/write", "2026-03-29T00:00:00Z"),
    )
