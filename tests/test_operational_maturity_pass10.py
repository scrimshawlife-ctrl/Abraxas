from __future__ import annotations

from abx.operations.failure_domains import failure_domain_audit_report
from abx.operations.incidents import build_incident_summary, build_rollback_plan, summarize_rollback_execution
from abx.operations.operating_manual import build_operating_manual
from abx.operations.runbooks import build_runbooks, summarize_runbook_execution, validate_runbooks
from abx.operations.service_expectations import expectation_report


def test_runbooks_are_deterministic_and_valid() -> None:
    a = validate_runbooks()
    b = validate_runbooks()
    assert a == b
    assert a["status"] in {"VALID", "BROKEN"}

    runbooks = build_runbooks()
    assert len(runbooks) >= 4
    summary = summarize_runbook_execution(runbooks[0].runbook_id)
    assert summary.status == "PLANNED"


def test_incident_and_rollback_reports_are_stable() -> None:
    a = build_incident_summary()
    b = build_incident_summary()
    assert a.__dict__ == b.__dict__

    first_incident = a.incidents[0]["incident_id"]
    plan_a = build_rollback_plan(first_incident)
    plan_b = build_rollback_plan(first_incident)
    assert plan_a.__dict__ == plan_b.__dict__

    exec_summary = summarize_rollback_execution(first_incident)
    assert exec_summary.status in {"PLANNED", "UNSUPPORTED"}


def test_failure_domains_and_expectations_are_stable() -> None:
    domain_a = failure_domain_audit_report()
    domain_b = failure_domain_audit_report()
    assert domain_a == domain_b
    assert domain_a["domainCount"] >= 3

    exp_a = expectation_report()
    exp_b = expectation_report()
    assert exp_a == exp_b
    statuses = {x["status"] for x in exp_a["expectations"]}
    assert "GUARANTEED" in statuses
    assert "ASPIRATIONAL" in statuses


def test_operating_manual_is_deterministic_and_sectioned() -> None:
    a = build_operating_manual()
    b = build_operating_manual()
    assert a.__dict__ == b.__dict__
    assert "runbooks" in a.sections
    assert "incident_response" in a.sections
    assert "service_expectations" in a.sections
