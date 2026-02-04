from __future__ import annotations

from abraxas.familiar.kernel.familiar_kernel import FamiliarKernel


def _policy_snapshot(grants):
    return {
        "schema_version": "v0",
        "policy_id": "policy-1",
        "issued_at": None,
        "capability_grants": grants,
        "metadata": None,
    }


def _grant(capability_id: str, granted: bool) -> dict:
    return {
        "schema_version": "v0",
        "capability_id": capability_id,
        "granted": granted,
        "reason": None,
        "constraints": None,
    }


def _run_request(run_id: str) -> dict:
    steps = [
        {"step_id": "beta", "action": "noop", "depends_on": ["alpha"], "parameters": None},
        {"step_id": "alpha", "action": "noop", "depends_on": [], "parameters": None},
        {"step_id": "gamma", "action": "noop", "depends_on": ["alpha"], "parameters": None},
    ]
    return {
        "schema_version": "v0",
        "run_id": run_id,
        "inputs": {"query": "signal"},
        "required_inputs": ["query"],
        "requested_capabilities": ["forager.read"],
        "steps": steps,
        "policy_snapshot": _policy_snapshot([_grant("forager.read", True)]),
        "metadata": None,
    }


def test_familiar_deterministic_plan_and_hash():
    req = _run_request("run-1")
    a = FamiliarKernel().run(req)
    b = FamiliarKernel().run(req)

    assert a["run_result"]["result_hash"] == b["run_result"]["result_hash"]
    assert a["ledger_event"]["event_hash"] == b["ledger_event"]["event_hash"]
    assert a["run_plan"]["ordered_step_ids"] == ["alpha", "beta", "gamma"]
    assert b["run_plan"]["ordered_step_ids"] == ["alpha", "beta", "gamma"]
