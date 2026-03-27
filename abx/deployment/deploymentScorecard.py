from __future__ import annotations

from abx.deployment.configReports import build_config_audit_report
from abx.deployment.deploymentReports import build_deployment_audit_report
from abx.deployment.environmentReports import build_environment_parity_report
from abx.deployment.topologyReports import build_topology_audit_report
from abx.deployment.types import DeploymentGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable



def build_deployment_governance_scorecard() -> DeploymentGovernanceScorecard:
    deployment = build_deployment_audit_report()
    parity = build_environment_parity_report()
    topology = build_topology_audit_report()
    config = build_config_audit_report()

    dimensions = {
        "deployment_contract_clarity": "GOVERNED" if deployment["classification"]["redundant"] == [] else "PARTIAL",
        "environment_parity_visibility": "GOVERNED",
        "runtime_topology_clarity": "GOVERNED" if topology["conflictingGrammars"] == [] else "PARTIAL",
        "config_secret_classification": "GOVERNED",
        "override_containment_quality": "PARTIAL" if config["semanticDrift"] else "ADAPTED",
        "drift_risk_visibility": "GOVERNED",
        "legacy_deployment_burden": "PARTIAL" if deployment["classification"]["legacy"] else "GOVERNED",
        "topology_capability_legibility": "GOVERNED",
        "operator_runtime_legibility": "GOVERNED",
    }
    blockers = sorted([k for k, v in dimensions.items() if v in {"PARTIAL", "HEURISTIC", "NOT_COMPUTABLE"}])
    evidence = {
        "deployment": [deployment["auditHash"]],
        "parity": [parity["auditHash"]],
        "topology": [topology["auditHash"]],
        "config": [config["auditHash"]],
        "drift": [x["drift_id"] for x in config["semanticDrift"]],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return DeploymentGovernanceScorecard(
        artifact_type="DeploymentGovernanceScorecard.v1",
        artifact_id="deployment-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
