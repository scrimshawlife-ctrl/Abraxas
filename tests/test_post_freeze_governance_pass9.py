from __future__ import annotations

from pathlib import Path

from abx.governance.baseline_enforcement import run_baseline_enforcement
from abx.governance.change_control import build_change_control_request
from abx.governance.maintenance_cycle import run_maintenance_cycle
from abx.governance.upgrade_plan import build_governed_upgrade_plan
from abx.governance.waivers import build_waiver_audit


def test_baseline_enforcement_is_deterministic() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    a = run_baseline_enforcement(repo_root=repo_root)
    b = run_baseline_enforcement(repo_root=repo_root)
    assert a.__dict__ == b.__dict__
    assert a.status in {"PASS", "WARN", "FAIL"}


def test_change_control_request_classification_stability() -> None:
    payload = {
        "request_id": "CCR-001",
        "changed_paths": ["abx/resonance_frame.py", "abx/governance/canonical_manifest.py"],
    }
    a = build_change_control_request(payload)
    b = build_change_control_request(payload)
    assert a.__dict__ == b.__dict__
    assert a.risk_status in {"INTERNAL_ONLY", "ADDITIVE_SAFE", "MIGRATION_REQUIRED", "BREAKING"}


def test_upgrade_plan_and_waiver_audit_stability() -> None:
    plan_a = build_governed_upgrade_plan({"baseline_to": "ABX-GOV-BASELINE-002", "target_version": "v1.1.0-rc0"})
    plan_b = build_governed_upgrade_plan({"baseline_to": "ABX-GOV-BASELINE-002", "target_version": "v1.1.0-rc0"})
    assert plan_a.__dict__ == plan_b.__dict__
    assert plan_a.readiness_state in {"READY_FOR_REVIEW", "NEEDS_MIGRATION_BUNDLE", "BLOCKED", "NOT_COMPUTABLE"}

    waiver_a = build_waiver_audit()
    waiver_b = build_waiver_audit()
    assert waiver_a.__dict__ == waiver_b.__dict__


def test_maintenance_cycle_stability() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    cycle_a, summary_a = run_maintenance_cycle(repo_root=repo_root, cycle_id="cycle-test")
    cycle_b, summary_b = run_maintenance_cycle(repo_root=repo_root, cycle_id="cycle-test")

    assert cycle_a.__dict__ == cycle_b.__dict__
    assert summary_a.__dict__ == summary_b.__dict__
    assert cycle_a.cycle_state in {"HEALTHY", "NEEDS_REVIEW", "WAIVER_STALE", "UPGRADE_BACKLOG", "BASELINE_DRIFT_RISK", "NOT_COMPUTABLE"}
