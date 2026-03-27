from __future__ import annotations

from abx.performance.accountingReports import build_resource_accounting_report
from abx.performance.budgetReports import build_budget_audit_report
from abx.performance.performanceReports import build_performance_surface_report
from abx.performance.timingReports import build_latency_throughput_overhead_report
from abx.performance.types import PerformanceResourceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_performance_resource_scorecard() -> PerformanceResourceScorecard:
    surface = build_performance_surface_report()
    accounting = build_resource_accounting_report()
    timing = build_latency_throughput_overhead_report()
    budget = build_budget_audit_report()

    dimensions = {
        "performance_surface_clarity": "GOVERNED" if not surface["vocabularyConflicts"] else "PARTIAL",
        "accounting_coverage": "PARTIAL" if accounting["modeClassification"]["not_computable"] else "GOVERNED",
        "latency_visibility_quality": "GOVERNED",
        "throughput_constraint_visibility": "GOVERNED",
        "overhead_attribution_quality": "GOVERNED",
        "budget_quota_throttle_clarity": "GOVERNED" if not budget["hiddenDrift"] else "PARTIAL",
        "resource_drift_visibility": "PARTIAL" if budget["budgetState"]["degraded"] else "GOVERNED",
        "legacy_performance_burden": "PARTIAL" if surface["classification"]["legacy_redundant_candidate"] else "GOVERNED",
        "environment_performance_parity_visibility": "MONITORED",
        "operator_legibility": "GOVERNED",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"PARTIAL", "HEURISTIC", "NOT_COMPUTABLE"})
    evidence = {
        "surface": [surface["auditHash"]],
        "accounting": [accounting["auditHash"]],
        "timing": [timing["auditHash"]],
        "budget": [budget["auditHash"]],
        "degradedBudgets": budget["budgetState"]["degraded"],
        "notComputableAccounting": accounting["modeClassification"]["not_computable"],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return PerformanceResourceScorecard(
        artifact_type="PerformanceResourceScorecard.v1",
        artifact_id="performance-resource-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
