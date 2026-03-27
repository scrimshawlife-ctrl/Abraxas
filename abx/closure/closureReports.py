from __future__ import annotations

from pathlib import Path

from abx.closure.closureClassification import classify_domain_closure_state, classify_system_closure_state
from abx.closure.closureDependencies import classify_dependency_states
from abx.closure.closureInventory import build_closure_surface_inventory
from abx.closure.types import SystemClosureRecord
from abx.deployment.deploymentScorecard import build_deployment_governance_scorecard
from abx.docs_governance.docScorecard import build_doc_legibility_scorecard
from abx.epistemics.epistemicScorecard import build_epistemic_quality_scorecard
from abx.governance.health_scorecard import build_repo_health_scorecard
from abx.innovation.innovationScorecard import build_experimentation_governance_scorecard
from abx.meta.metaScorecard import build_meta_governance_scorecard
from abx.performance.performanceScorecard import build_performance_resource_scorecard
from abx.productization.productScorecard import build_productization_governance_scorecard
from abx.security.securityScorecard import build_security_integrity_scorecard


DOMAIN_SCORECARD_BUILDERS = {
    "domain.baseline": lambda: build_repo_health_scorecard(repo_root=Path(".")),
    "domain.security": build_security_integrity_scorecard,
    "domain.deployment": build_deployment_governance_scorecard,
    "domain.epistemic": build_epistemic_quality_scorecard,
    "domain.docs": build_doc_legibility_scorecard,
    "domain.product": build_productization_governance_scorecard,
    "domain.performance": build_performance_resource_scorecard,
    "domain.innovation": build_experimentation_governance_scorecard,
    "domain.meta": build_meta_governance_scorecard,
}


def build_closure_domain_evidence() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for row in build_closure_surface_inventory():
        scorecard = DOMAIN_SCORECARD_BUILDERS[row.domain_id]()
        blockers = sorted(getattr(scorecard, "blockers", []))
        evidence_ref = getattr(scorecard, "scorecard_hash", "")
        out[row.domain_id] = {
            "artifactType": getattr(scorecard, "artifact_type", row.upstream_artifact),
            "blockers": blockers,
            "evidenceRef": evidence_ref,
            "waiverIds": sorted(row.waiver_ids),
        }
    return out


def build_system_closure_record() -> SystemClosureRecord:
    inventory = build_closure_surface_inventory()
    evidence_by_domain = build_closure_domain_evidence()

    domain_states: dict[str, str] = {}
    waived_domains: list[str] = []
    blocked_domains: list[str] = []
    degraded_domains: list[str] = []
    partial_domains: list[str] = []
    evidence_refs: list[str] = []

    for row in inventory:
        evidence = evidence_by_domain[row.domain_id]
        state = classify_domain_closure_state(evidence["blockers"], evidence["waiverIds"])
        domain_states[row.domain_id] = state
        if state == "CLOSURE_COMPLETE_WITH_WAIVERS":
            waived_domains.append(row.domain_id)
        elif state == "BLOCKED":
            blocked_domains.append(row.domain_id)
        elif state == "DEGRADED":
            degraded_domains.append(row.domain_id)
        elif state not in {"CLOSURE_COMPLETE", "CLOSURE_COMPLETE_WITH_WAIVERS"}:
            partial_domains.append(row.domain_id)
        evidence_refs.append(str(evidence["evidenceRef"]))

    dependency_states = classify_dependency_states(domain_states)
    closure_state = classify_system_closure_state(domain_states, dependency_states)

    return SystemClosureRecord(
        record_id="system-closure-record",
        closure_state=closure_state,
        domain_states=domain_states,
        dependency_states=dependency_states,
        waived_domains=sorted(waived_domains),
        blocked_domains=sorted(blocked_domains),
        degraded_domains=sorted(degraded_domains),
        partial_domains=sorted(partial_domains),
        evidence_refs=sorted(evidence_refs),
    )


def build_system_closure_report() -> dict[str, object]:
    record = build_system_closure_record()
    return {
        "artifactType": "SystemClosureReport.v1",
        "artifactId": "system-closure-report",
        "record": record.__dict__,
        "summary": {
            "closedDomains": sorted(k for k, v in record.domain_states.items() if v == "CLOSURE_COMPLETE"),
            "waivedDomains": record.waived_domains,
            "blockedDomains": record.blocked_domains,
            "degradedDomains": record.degraded_domains,
            "partialDomains": record.partial_domains,
        },
    }
