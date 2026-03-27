from __future__ import annotations

from abx.knowledge.carryForwardChecks import run_carry_forward_checks
from abx.knowledge.continuityCoverage import build_continuity_coverage
from abx.knowledge.continuityReports import build_continuity_audit_report
from abx.knowledge.forgettingReports import build_forgetting_report
from abx.knowledge.knowledgeClassification import classify_knowledge_surfaces
from abx.knowledge.knowledgeInventory import classify_active_vs_historical
from abx.knowledge.knowledgeReports import build_knowledge_audit_report
from abx.knowledge.knowledgeScorecard import build_knowledge_continuity_scorecard
from abx.knowledge.memoryLifecycle import build_memory_lifecycle
from abx.knowledge.memoryTransitions import validate_memory_transitions
from abx.knowledge.retentionPolicy import build_retention_policy
from abx.knowledge.staleMemoryDetection import detect_stale_memory


def test_knowledge_surface_classification_and_activity_state_stability() -> None:
    a = classify_knowledge_surfaces()
    b = classify_knowledge_surfaces()
    assert a == b

    states = [x.activity_state for x in classify_active_vs_historical()]
    assert "ACTIVE" in states
    assert "HISTORICAL" in states

    assert build_knowledge_audit_report() == build_knowledge_audit_report()


def test_memory_lifecycle_retention_and_stale_detection() -> None:
    rows = build_memory_lifecycle()
    assert rows
    assert build_retention_policy()
    transitions = validate_memory_transitions()
    assert transitions["violations"] == []
    stale = detect_stale_memory()
    assert isinstance(stale, list)


def test_continuity_linkage_coverage_and_report_determinism() -> None:
    coverage = build_continuity_coverage(run_id="RUN-1")
    assert coverage.complete is True
    a = build_continuity_audit_report(run_id="RUN-1")
    b = build_continuity_audit_report(run_id="RUN-1")
    assert a == b


def test_carry_forward_and_forgetting_audits_are_deterministic() -> None:
    a = run_carry_forward_checks()
    b = run_carry_forward_checks()
    assert a == b

    f1 = build_forgetting_report()
    f2 = build_forgetting_report()
    assert f1 == f2


def test_knowledge_continuity_scorecard_determinism_and_blockers() -> None:
    a = build_knowledge_continuity_scorecard(run_id="RUN-1")
    b = build_knowledge_continuity_scorecard(run_id="RUN-1")
    assert a.__dict__ == b.__dict__
    assert isinstance(a.blockers, list)
