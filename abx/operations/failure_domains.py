from __future__ import annotations

from dataclasses import asdict

from abx.operations.types import FailureDomainRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_failure_domain_map() -> list[FailureDomainRecord]:
    rows = [
        FailureDomainRecord(
            domain_id="domain.governance.enforcement",
            domain_group="governance",
            severity="high",
            affected_surfaces=["baseline_enforcement", "migration_guards", "breaking_scan"],
            evidence_surfaces=["BaselineEnforcementResult.v1", "MigrationGuardResult.v1", "BreakingChangeReport.v1"],
            response_runbook="incident-triage",
        ),
        FailureDomainRecord(
            domain_id="domain.runtime.proof_closure",
            domain_group="runtime",
            severity="high",
            affected_surfaces=["proof_chain", "closure_summary", "continuity"],
            evidence_surfaces=["ProofChainArtifact.v1", "ClosureSummaryArtifact.v1", "ContinuitySummaryArtifact.v1"],
            response_runbook="simulation-proof-closure",
        ),
        FailureDomainRecord(
            domain_id="domain.portfolio.arithmetic",
            domain_group="simulation",
            severity="critical",
            affected_surfaces=["paper_trading", "simulation_validation"],
            evidence_surfaces=["ValidationResultArtifact.v1"],
            response_runbook="simulation-proof-closure",
        ),
        FailureDomainRecord(
            domain_id="domain.operations.waiver_maintenance",
            domain_group="operations",
            severity="medium",
            affected_surfaces=["waivers", "maintenance_cycle"],
            evidence_surfaces=["WaiverAuditArtifact.v1", "MaintenanceSummaryArtifact.v1"],
            response_runbook="maintenance-cycle",
        ),
    ]
    return sorted(rows, key=lambda x: x.domain_id)


def failure_domain_audit_report() -> dict[str, object]:
    rows = build_failure_domain_map()
    payload = [asdict(x) for x in rows]
    digest = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return {
        "artifactType": "FailureDomainAuditArtifact.v1",
        "artifactId": "failure-domain-audit-abx",
        "domains": payload,
        "domainCount": len(rows),
        "auditHash": digest,
    }
