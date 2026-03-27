from __future__ import annotations

from abx.performance.accountingClassification import (
    classify_accounting_modes,
    detect_redundant_accounting_surfaces,
)
from abx.performance.accountingReports import build_resource_accounting_report
from abx.performance.budgetPolicies import budget_precedence, classify_budget_state
from abx.performance.budgetReports import build_budget_audit_report
from abx.performance.performanceClassification import (
    classify_performance_surfaces,
    detect_duplicate_performance_vocabulary,
)
from abx.performance.performanceReports import build_performance_surface_report
from abx.performance.performanceScorecard import build_performance_resource_scorecard
from abx.performance.quotaThrottleClassification import (
    detect_hidden_retry_or_throttle_drift,
    throttle_precedence_order,
)
from abx.performance.timingReports import build_latency_throughput_overhead_report
from abx.performance.throughputClassification import classify_throughput_constraints


def test_performance_surface_classification_and_report_determinism() -> None:
    assert classify_performance_surfaces() == classify_performance_surfaces()
    assert detect_duplicate_performance_vocabulary() == []
    report_a = build_performance_surface_report()
    report_b = build_performance_surface_report()
    assert report_a == report_b
    assert report_a["classification"]["critical_path"]


def test_accounting_mode_stability_and_attribution() -> None:
    modes = classify_accounting_modes()
    assert modes == classify_accounting_modes()
    assert len(modes["accounted"]) >= 2
    assert detect_redundant_accounting_surfaces() == []
    report = build_resource_accounting_report()
    assert report == build_resource_accounting_report()
    assert report["records"][0]["attribution_owner"]


def test_latency_throughput_overhead_visibility_stability() -> None:
    assert classify_throughput_constraints() == classify_throughput_constraints()
    report_a = build_latency_throughput_overhead_report()
    report_b = build_latency_throughput_overhead_report()
    assert report_a == report_b
    assert report_a["statusBreakdown"]["measured"]
    assert report_a["overheadAttribution"]["observability_overhead"]


def test_budget_quota_throttle_precedence_and_state_stability() -> None:
    state = classify_budget_state()
    assert state == classify_budget_state()
    assert state["degraded"] == ["budget.background.backfill_jobs"]
    assert budget_precedence() == budget_precedence()
    assert throttle_precedence_order() == throttle_precedence_order()
    assert detect_hidden_retry_or_throttle_drift() == []
    report = build_budget_audit_report()
    assert report == build_budget_audit_report()


def test_performance_resource_scorecard_determinism_and_blockers() -> None:
    a = build_performance_resource_scorecard()
    b = build_performance_resource_scorecard()
    assert a.__dict__ == b.__dict__
    assert "accounting_coverage" in a.blockers
    assert "resource_drift_visibility" in a.blockers
