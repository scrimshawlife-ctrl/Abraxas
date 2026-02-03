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
        {"step_id": "beta", "action": "noop", "depends_on": ["alpha"], "parameters": None},
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


def test_familiar_12_run_invariance():
    kernel = FamiliarKernel()
    req = _run_request("run-12")
    hashes = [kernel.run(req)["run_result"]["result_hash"] for _ in range(12)]

    assert len(set(hashes)) == 1
