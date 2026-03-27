from __future__ import annotations

from abx.closure.types import AuditSurfaceRecord


def build_audit_surface_inventory() -> list[AuditSurfaceRecord]:
    rows = [
        AuditSurfaceRecord(
            surface_id="bundle.whole_system",
            bundle_scope="whole-system-readiness",
            required_domains=["domain.baseline", "domain.security", "domain.deployment", "domain.epistemic", "domain.meta"],
            optional_domains=["domain.docs", "domain.performance", "domain.product", "domain.innovation"],
        ),
        AuditSurfaceRecord(
            surface_id="bundle.baseline_ratification",
            bundle_scope="baseline-ratification",
            required_domains=["domain.baseline", "domain.security", "domain.deployment", "domain.docs"],
            optional_domains=["domain.meta"],
        ),
        AuditSurfaceRecord(
            surface_id="bundle.exceptions",
            bundle_scope="exception-waiver",
            required_domains=["domain.meta", "domain.docs"],
            optional_domains=["domain.performance", "domain.product"],
        ),
    ]
    return sorted(rows, key=lambda x: x.surface_id)
