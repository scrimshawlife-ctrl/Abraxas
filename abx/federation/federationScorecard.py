from __future__ import annotations

from abx.federation.capabilityReports import build_capability_registry_report
from abx.federation.contractReports import build_cross_system_contract_report
from abx.federation.interopReports import build_interop_audit_report
from abx.federation.semanticAlignment import build_federated_semantic_alignment
from abx.federation.types import FederationGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_federation_governance_scorecard() -> FederationGovernanceScorecard:
    interop = build_interop_audit_report()
    contracts = build_cross_system_contract_report()
    alignment = build_federated_semantic_alignment()
    capabilities = build_capability_registry_report()

    dimensions = {
        "interop_path_clarity": "GOVERNED" if not interop["redundantPatterns"] else "PARTIAL",
        "cross_system_contract_coverage": "GOVERNED" if not contracts["duplicateShapes"] else "PARTIAL",
        "semantic_alignment_quality": "PARTIAL" if any(x.status == "adapted" for x in alignment) else "GOVERNED",
        "capability_registry_clarity": "GOVERNED",
        "handoff_provenance_trust_continuity": "GOVERNED",
        "legacy_interop_burden": "PARTIAL" if "derived" in interop["classification"] else "GOVERNED",
        "mismatch_visibility": "GOVERNED",
        "operator_federation_legibility": "GOVERNED",
    }
    evidence = {
        "interop": [interop["auditHash"]],
        "contracts": [contracts["auditHash"]],
        "alignment": [x.alignment_id for x in alignment],
        "capabilities": [capabilities["auditHash"]],
    }
    blockers = sorted([k for k, v in dimensions.items() if v == "PARTIAL"])
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return FederationGovernanceScorecard(
        artifact_type="FederationGovernanceScorecard.v1",
        artifact_id="federation-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
