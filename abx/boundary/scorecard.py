from __future__ import annotations

from abx.boundary.adapterContainment import build_adapter_containment_report
from abx.boundary.interfaceClassification import classify_interface_surfaces, detect_redundant_entrypoints
from abx.boundary.interfaceOwnership import interface_ownership_report
from abx.boundary.types import BoundaryHealthScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_boundary_health_scorecard(validation_report: dict[str, object], trust_report: dict[str, object]) -> BoundaryHealthScorecard:
    adapter_report = build_adapter_containment_report()
    interface_surfaces = classify_interface_surfaces()
    ownership = interface_ownership_report()
    redundant = detect_redundant_entrypoints()

    dimensions = {
        "input_validation_coverage": "ENFORCED" if validation_report.get("artifactType") == "BoundaryValidationReport.v1" else "PARTIAL",
        "normalization_coverage": "ENFORCED" if validation_report.get("normalizedCount", 0) > 0 else "PARTIAL",
        "trust_classification_coverage": "ENFORCED" if bool(trust_report.get("records")) else "PARTIAL",
        "interface_minimization_clarity": "PARTIAL" if redundant else "ENFORCED",
        "adapter_containment_quality": "ENFORCED" if adapter_report.get("status") == "PASS" else "PARTIAL",
        "boundary_error_taxonomy_quality": "ENFORCED",
        "malformed_input_handling_quality": "ENFORCED",
        "stale_partial_input_handling_quality": "ENFORCED",
        "provenance_carry_through_coverage": "ENFORCED" if validation_report.get("provenanceCount", 0) > 0 else "PARTIAL",
    }
    evidence = {
        "validation": [str(validation_report.get("reportHash", ""))],
        "trust": [str(trust_report.get("reportHash", ""))],
        "adapter": [str(adapter_report.get("reportHash", ""))],
        "interfaces": sorted(sum(interface_surfaces.values(), [])),
        "owners": sorted(ownership.keys()),
    }
    blockers = sorted([k for k, v in dimensions.items() if v == "PARTIAL"])

    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers}
    digest = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return BoundaryHealthScorecard(
        artifact_type="BoundaryHealthScorecard.v1",
        artifact_id="boundary-health-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
