from __future__ import annotations

from abx.closure.auditInventory import build_audit_surface_inventory
from abx.closure.closureReports import build_closure_domain_evidence, build_system_closure_record
from abx.closure.types import EvidenceBundleRecord


def _stale_refs_for_domain(domain_id: str, blockers: list[str], evidence_ref: str) -> list[str]:
    if any("stale" in blocker for blocker in blockers):
        return [f"{domain_id}:{evidence_ref}"]
    return []


def build_evidence_bundles() -> list[EvidenceBundleRecord]:
    closure_record = build_system_closure_record()
    by_domain = build_closure_domain_evidence()
    out: list[EvidenceBundleRecord] = []

    for surface in build_audit_surface_inventory():
        included: list[str] = []
        missing: list[str] = []
        stale: list[str] = []
        blocked = [d for d in closure_record.blocked_domains if d in surface.required_domains]
        domains = sorted(set(surface.required_domains + surface.optional_domains))
        for domain_id in domains:
            domain = by_domain.get(domain_id)
            if domain is None:
                if domain_id in surface.required_domains:
                    missing.append(domain_id)
                continue
            ref = f"{domain_id}:{domain['evidenceRef']}"
            included.append(ref)
            stale.extend(_stale_refs_for_domain(domain_id, domain["blockers"], str(domain["evidenceRef"])))

        out.append(
            EvidenceBundleRecord(
                bundle_id=surface.surface_id,
                scope=surface.bundle_scope,
                included_evidence=sorted(included),
                missing_required_domains=sorted(missing),
                stale_evidence_refs=sorted(stale),
                blocked_domains=sorted(blocked),
            )
        )
    return out
