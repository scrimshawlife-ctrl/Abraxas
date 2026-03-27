from __future__ import annotations

from dataclasses import asdict

from abx.operations.failure_domains import build_failure_domain_map
from abx.resilience.types import FaultInjectionArtifact, ResilienceEvidence
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable

# Deterministic domain-scoped injection primitives.
_INJECTION_BY_DOMAIN = {
    "domain.governance.enforcement": [
        {"domain": "domain.governance.enforcement", "surface": "validation", "mode": "VALIDATION_FAILURE"},
        {"domain": "domain.governance.enforcement", "surface": "invariants", "mode": "INVARIANT_BREAK"},
    ],
    "domain.runtime.proof_closure": [
        {"domain": "domain.runtime.proof_closure", "surface": "scheduler", "mode": "SCHEDULER_DISRUPTION"},
        {"domain": "domain.runtime.proof_closure", "surface": "execution", "mode": "DELAYED_PARTIAL_EXECUTION"},
    ],
    "domain.portfolio.arithmetic": [
        {"domain": "domain.portfolio.arithmetic", "surface": "artifacts", "mode": "MISSING_ARTIFACT"},
    ],
    "domain.operations.waiver_maintenance": [
        {"domain": "domain.operations.waiver_maintenance", "surface": "execution", "mode": "DELAYED_PARTIAL_EXECUTION"},
    ],
}


def plan_fault_injection(scenario_id: str, domain_ids: list[str] | None = None) -> FaultInjectionArtifact:
    known_domains = [row.domain_id for row in build_failure_domain_map()]
    selected_domains = sorted(domain_ids or known_domains)

    plan: list[dict[str, str]] = []
    evidence: list[ResilienceEvidence] = []
    unknown_domains: list[str] = []
    for domain_id in selected_domains:
        injections = _INJECTION_BY_DOMAIN.get(domain_id)
        if not injections:
            unknown_domains.append(domain_id)
            continue
        plan.extend(injections)
        evidence.append(
            ResilienceEvidence(
                evidence_id=f"evidence.{domain_id}",
                source="failure-domain-map",
                detail=f"scoped deterministic injections for {domain_id}",
            )
        )

    status = "READY" if not unknown_domains else "PARTIAL"
    if unknown_domains:
        evidence.append(
            ResilienceEvidence(
                evidence_id="evidence.unknown-domains",
                source="fault-injection",
                detail=f"missing injection mapping for {','.join(sorted(unknown_domains))}",
            )
        )

    payload = {
        "scenario_id": scenario_id,
        "selected_domains": selected_domains,
        "status": status,
        "plan": plan,
        "evidence": [asdict(x) for x in evidence],
    }
    injection_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return FaultInjectionArtifact(
        artifact_type="FaultInjectionArtifact.v1",
        artifact_id=f"fault-injection-{scenario_id}",
        scenario_id=scenario_id,
        injection_plan=plan,
        injected_domains=selected_domains,
        status=status,
        evidence=evidence,
        injection_hash=injection_hash,
    )


def render_fault_injection_report(scenario_id: str, domain_ids: list[str] | None = None) -> dict[str, object]:
    artifact = plan_fault_injection(scenario_id=scenario_id, domain_ids=domain_ids)
    return {
        "artifactType": artifact.artifact_type,
        "artifactId": artifact.artifact_id,
        "scenarioId": artifact.scenario_id,
        "status": artifact.status,
        "injectedDomains": artifact.injected_domains,
        "injectionPlan": artifact.injection_plan,
        "evidence": [asdict(x) for x in artifact.evidence],
        "injectionHash": artifact.injection_hash,
    }
