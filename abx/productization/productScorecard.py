from __future__ import annotations

from abx.productization.audienceReports import build_audience_legibility_audit_report
from abx.productization.outputReports import build_output_boundedness_audit_report
from abx.productization.packageReports import build_packaging_audit_report
from abx.productization.productReports import build_product_surface_audit_report
from abx.productization.types import ProductizationGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_productization_governance_scorecard() -> ProductizationGovernanceScorecard:
    surface = build_product_surface_audit_report()
    packaging = build_packaging_audit_report()
    audience = build_audience_legibility_audit_report()
    output = build_output_boundedness_audit_report()

    dimensions = {
        "product_surface_clarity": "GOVERNED" if not surface["duplicates"] else "PARTIAL",
        "packaging_contract_quality": "PARTIAL" if packaging["compatibility"]["partial"] else "GOVERNED",
        "audience_legibility": "PARTIAL" if audience["coverage"]["partial"] else "GOVERNED",
        "boundedness_safety_coverage": "GOVERNED",
        "external_output_interpretability": "PARTIAL" if output["boundednessClassification"]["caution_required"] else "GOVERNED",
        "wrapper_duplication_burden": "GOVERNED" if not packaging["redundantDialects"] else "PARTIAL",
        "internal_external_separation_clarity": "GOVERNED",
        "legacy_experimental_exposure_burden": "PARTIAL" if surface["classification"]["legacy"] or surface["classification"]["experimental"] else "GOVERNED",
        "supportability_operational_legibility": "MONITORED",
        "tier_semantic_consistency": "GOVERNED",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"PARTIAL", "OVERLOADED", "NOT_COMPUTABLE"})
    evidence = {
        "surface": [surface["auditHash"]],
        "packaging": [packaging["auditHash"]],
        "audience": [audience["auditHash"]],
        "output": [output["auditHash"]],
        "partialPackages": packaging["compatibility"]["partial"],
        "cautionOutputs": output["boundednessClassification"]["caution_required"],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return ProductizationGovernanceScorecard(
        artifact_type="ProductizationGovernanceScorecard.v1",
        artifact_id="productization-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
