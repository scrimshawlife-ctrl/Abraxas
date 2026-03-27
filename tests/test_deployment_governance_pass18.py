from __future__ import annotations

from abx.deployment.configClassification import build_config_classifications, classify_config_surface
from abx.deployment.configReports import build_config_audit_report
from abx.deployment.deploymentClassification import (
    classify_deployment_surfaces,
    deployment_ownership_summary,
    detect_duplicate_deployment_entrypoints,
)
from abx.deployment.deploymentReports import build_deployment_audit_report
from abx.deployment.deploymentScorecard import build_deployment_governance_scorecard
from abx.deployment.environmentClassification import classify_environment_taxonomy, detect_redundant_environment_taxonomy
from abx.deployment.environmentParity import classify_parity_status
from abx.deployment.environmentReports import build_environment_parity_report
from abx.deployment.overrideContainment import detect_hidden_semantic_drift, override_precedence_summary
from abx.deployment.runtimeTopology import classify_runtime_topologies, detect_conflicting_topology_grammars
from abx.deployment.topologyCapabilities import build_topology_capabilities
from abx.deployment.topologyReports import build_topology_audit_report



def test_deployment_contract_governance_determinism() -> None:
    assert classify_deployment_surfaces() == classify_deployment_surfaces()
    assert deployment_ownership_summary() == deployment_ownership_summary()
    assert detect_duplicate_deployment_entrypoints() == []
    report = build_deployment_audit_report()
    assert report == build_deployment_audit_report()
    assert "environmentContracts" in report



def test_environment_parity_and_drift_classification_stability() -> None:
    assert classify_environment_taxonomy() == classify_environment_taxonomy()
    assert classify_parity_status() == classify_parity_status()
    assert detect_redundant_environment_taxonomy() == []
    assert build_environment_parity_report() == build_environment_parity_report()



def test_runtime_topology_and_capability_stability() -> None:
    assert classify_runtime_topologies() == classify_runtime_topologies()
    a = [x.__dict__ for x in build_topology_capabilities()]
    b = [x.__dict__ for x in build_topology_capabilities()]
    assert a == b
    assert detect_conflicting_topology_grammars() == []
    assert build_topology_audit_report() == build_topology_audit_report()



def test_config_secret_override_containment_stability() -> None:
    assert [x.__dict__ for x in build_config_classifications()] == [x.__dict__ for x in build_config_classifications()]
    assert classify_config_surface() == classify_config_surface()
    assert override_precedence_summary() == override_precedence_summary()
    assert [x.__dict__ for x in detect_hidden_semantic_drift()] == [x.__dict__ for x in detect_hidden_semantic_drift()]
    report = build_config_audit_report()
    assert report == build_config_audit_report()
    assert len(report["semanticDrift"]) >= 1



def test_deployment_scorecard_determinism_and_blockers() -> None:
    a = build_deployment_governance_scorecard()
    b = build_deployment_governance_scorecard()
    assert a.__dict__ == b.__dict__
    assert isinstance(a.blockers, list)
    assert "override_containment_quality" in a.blockers
