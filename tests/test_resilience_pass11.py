from __future__ import annotations

from abx.resilience.degradation import evaluate_degradation
from abx.resilience.faultInjection import plan_fault_injection
from abx.resilience.recoveryDrills import run_recovery_drill
from abx.resilience.scorecard import build_resilience_scorecard
from abx.resilience.training import run_training_scenario


def test_fault_injection_is_deterministic_and_scoped() -> None:
    a = plan_fault_injection("pass11")
    b = plan_fault_injection("pass11")
    assert a.__dict__ == b.__dict__
    assert a.status in {"READY", "PARTIAL"}
    assert all(step["domain"].startswith("domain.") for step in a.injection_plan)


def test_recovery_drill_validates_expected_vs_actual() -> None:
    artifact = run_recovery_drill("pass11", mode="containment")
    assert artifact.status in {"PASS", "FAIL"}
    assert set(artifact.comparison.values()).issubset({"MATCH", "MISSING"})
    assert artifact.expected_outcomes


def test_degradation_classification_is_explicit() -> None:
    artifact = evaluate_degradation("pass11", subsystem="runtime")
    assert artifact.state in {"FULL", "DEGRADED", "LIMITED", "BLOCKED"}
    assert artifact.fallback_actions


def test_training_scenario_is_repeatable() -> None:
    a = run_training_scenario("pass11", drill_mode="containment")
    b = run_training_scenario("pass11", drill_mode="containment")
    assert a.__dict__ == b.__dict__
    assert a.evaluation_summary["status"] in {"PASS", "FAIL"}


def test_resilience_scorecard_is_stable_and_evidence_backed() -> None:
    a = build_resilience_scorecard("pass11")
    b = build_resilience_scorecard("pass11")
    assert a.__dict__ == b.__dict__
    assert set(a.dimensions) == {
        "failure_coverage",
        "recovery_success",
        "degradation_clarity",
        "operator_readiness",
        "invariance_under_stress",
    }
    assert isinstance(a.blockers, list)


def test_invariance_under_injected_failure() -> None:
    fault_a = plan_fault_injection("pass11", domain_ids=["domain.runtime.proof_closure"])
    fault_b = plan_fault_injection("pass11", domain_ids=["domain.runtime.proof_closure"])
    drill_a = run_recovery_drill("pass11", mode="containment")
    drill_b = run_recovery_drill("pass11", mode="containment")

    assert fault_a.injection_hash == fault_b.injection_hash
    assert drill_a.drill_hash == drill_b.drill_hash
