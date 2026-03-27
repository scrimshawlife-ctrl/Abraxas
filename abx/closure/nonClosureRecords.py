from __future__ import annotations

from abx.closure.auditReports import build_audit_readiness_record
from abx.closure.closureReports import build_system_closure_record
from abx.closure.types import NonClosureRecord


def build_non_closure_records() -> list[NonClosureRecord]:
    closure = build_system_closure_record()
    audit = build_audit_readiness_record()
    rows: list[NonClosureRecord] = []

    for domain_id in closure.blocked_domains:
        rows.append(
            NonClosureRecord(
                non_closure_id=f"non-closure.blocked.{domain_id}",
                classification="blocking",
                domain_id=domain_id,
                reason="domain_blocked_for_closure",
                evidence_ref=f"closure:{domain_id}",
            )
        )
    for domain_id in closure.waived_domains:
        rows.append(
            NonClosureRecord(
                non_closure_id=f"non-closure.waived.{domain_id}",
                classification="waived",
                domain_id=domain_id,
                reason="domain_accepted_with_waiver",
                evidence_ref=f"closure:{domain_id}",
            )
        )
    for bundle_id in audit.stale_bundles:
        rows.append(
            NonClosureRecord(
                non_closure_id=f"non-closure.stale.{bundle_id}",
                classification="stale_exception",
                domain_id=bundle_id,
                reason="audit_bundle_has_stale_evidence",
                evidence_ref=f"audit:{bundle_id}",
            )
        )
    for bundle_id in audit.incomplete_bundles:
        rows.append(
            NonClosureRecord(
                non_closure_id=f"non-closure.unresolved.{bundle_id}",
                classification="unresolved",
                domain_id=bundle_id,
                reason="audit_bundle_missing_required_evidence",
                evidence_ref=f"audit:{bundle_id}",
            )
        )
    return sorted(rows, key=lambda x: x.non_closure_id)
