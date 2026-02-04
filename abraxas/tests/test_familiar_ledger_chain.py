from __future__ import annotations

from abraxas.familiar.kernel.familiar_kernel import FamiliarKernel
from abraxas.familiar.ledger.hash_chain import validate_chain


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
        "requested_capabilities": ["forager.read"],
        "steps": steps,
        "policy_snapshot": _policy_snapshot([_grant("forager.read", True)]),
        "metadata": None,
    }


def test_familiar_ledger_chain_integrity():
    kernel = FamiliarKernel()
    kernel.run(_run_request("run-ledger-1"))
    kernel.run(_run_request("run-ledger-2"))

    events = list(kernel.ledger_store.read_all())
    assert len(events) == 2
    assert events[1]["prev_hash"] == events[0]["event_hash"]
    assert validate_chain(events) is True
