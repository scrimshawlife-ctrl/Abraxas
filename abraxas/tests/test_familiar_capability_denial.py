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
        {"step_id": "alpha", "action": "noop", "depends_on": [], "parameters": None},
    ]
    return {
        "schema_version": "v0",
        "run_id": run_id,
        "inputs": {"query": "signal"},
        "required_inputs": ["query"],
        "requested_capabilities": ["forager.write"],
        "steps": steps,
        "policy_snapshot": _policy_snapshot([_grant("forager.read", True)]),
        "metadata": None,
    }


def test_familiar_capability_denial_reason_code():
    kernel = FamiliarKernel()
    result = kernel.run(_run_request("run-deny"))

    run_result = result["run_result"]
    assert run_result["not_computable"] is True
    assert run_result["reason_code"] == "capability_denied"
    assert result["capability_decision"]["denied_capabilities"] == ["forager.write"]
