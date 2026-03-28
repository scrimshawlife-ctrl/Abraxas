from __future__ import annotations

from abx.operator.types import HumanOverrideRecord


def build_override_inventory() -> tuple[HumanOverrideRecord, ...]:
    return (
        HumanOverrideRecord(
            override_id="ovr.emergency.feed-freeze.001",
            surface="boundary.ingest.external-feed",
            requested_by="operator.incident",
            authority_ref="apr.override.001",
            justification="Contain active ingestion fault while integrity checks run",
            override_scope="connector/external-feed/freeze",
            bypass_boundary="policy.boundary.validation",
            requested_at="2026-03-27T08:00:00Z",
            expires_at="2026-03-28T02:00:00Z",
            status_signal="approved_active",
        ),
        HumanOverrideRecord(
            override_id="ovr.maintenance.queue-throttle.001",
            surface="capacity.scheduler.priority-queue",
            requested_by="operator.runtime",
            authority_ref="apr.deploy.001",
            justification="Temporary queue throttle for maintenance migration",
            override_scope="scheduler/priority/throttle-20",
            bypass_boundary="policy.capacity.contention",
            requested_at="2026-03-27T02:00:00Z",
            expires_at="2026-03-29T00:00:00Z",
            status_signal="requested",
        ),
        HumanOverrideRecord(
            override_id="ovr.policy-disable.identity.001",
            surface="identity.resolution.persistence",
            requested_by="operator.admin",
            authority_ref="",
            justification="Disable checks to speed an ad-hoc import",
            override_scope="identity/checks/off",
            bypass_boundary="policy.identity.referential-coherence",
            requested_at="2026-03-27T03:10:00Z",
            expires_at="2026-04-30T00:00:00Z",
            status_signal="forbidden",
        ),
        HumanOverrideRecord(
            override_id="ovr.release.rollback.001",
            surface="deployment.release.promotion",
            requested_by="operator.release",
            authority_ref="apr.destroy.001",
            justification="Rollback requested but denied by steward",
            override_scope="release/rollback/v21",
            bypass_boundary="policy.admission.promotion-gates",
            requested_at="2026-03-27T07:00:00Z",
            expires_at="2026-03-27T12:00:00Z",
            status_signal="denied",
        ),
    )
