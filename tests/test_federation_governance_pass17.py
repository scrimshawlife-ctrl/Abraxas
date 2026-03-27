from __future__ import annotations

from abx.federation.capabilityDependencies import build_capability_dependencies
from abx.federation.capabilityReports import build_capability_registry_report
from abx.federation.contractCompatibility import classify_contract_compatibility, detect_duplicate_contract_shapes
from abx.federation.contractReports import build_cross_system_contract_report
from abx.federation.federationScorecard import build_federation_governance_scorecard
from abx.federation.handoffEnvelopes import build_handoff_envelopes
from abx.federation.interopClassification import classify_interop_paths, detect_redundant_interop_patterns
from abx.federation.interopReports import build_interop_audit_report
from abx.federation.semanticAlignment import build_federated_semantic_alignment


def test_interop_classification_handoff_and_report_determinism() -> None:
    assert classify_interop_paths() == classify_interop_paths()
    assert detect_redundant_interop_patterns() == []
    assert [x.__dict__ for x in build_handoff_envelopes()] == [x.__dict__ for x in build_handoff_envelopes()]
    assert build_interop_audit_report() == build_interop_audit_report()


def test_cross_system_contract_governance_stability() -> None:
    assert classify_contract_compatibility() == classify_contract_compatibility()
    assert detect_duplicate_contract_shapes() == []
    assert build_cross_system_contract_report() == build_cross_system_contract_report()


def test_federated_semantic_alignment_stability() -> None:
    a = [x.__dict__ for x in build_federated_semantic_alignment()]
    b = [x.__dict__ for x in build_federated_semantic_alignment()]
    assert a == b
    statuses = {x["status"] for x in a}
    assert statuses.issubset({"aligned", "adapted", "mismatched", "legacy-tolerated", "not-computable"})


def test_capability_registry_dependency_and_report_stability() -> None:
    deps_a = [x.__dict__ for x in build_capability_dependencies()]
    deps_b = [x.__dict__ for x in build_capability_dependencies()]
    assert deps_a == deps_b
    assert build_capability_registry_report() == build_capability_registry_report()


def test_federation_scorecard_determinism_and_blockers() -> None:
    a = build_federation_governance_scorecard()
    b = build_federation_governance_scorecard()
    assert a.__dict__ == b.__dict__
    assert isinstance(a.blockers, list)
