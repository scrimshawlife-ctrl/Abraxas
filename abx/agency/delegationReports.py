from __future__ import annotations

from abx.agency.delegationClassification import classify_delegation_posture
from abx.agency.delegationInventory import build_delegation_inventory
from abx.agency.delegationRecords import build_delegation_chains
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_delegation_report() -> dict[str, object]:
    inventory = build_delegation_inventory()
    chains = build_delegation_chains()
    chain_states = {x.chain_id: x.recursion_state for x in chains}
    report = {
        "artifactType": "DelegationAudit.v1",
        "artifactId": "delegation-audit",
        "delegations": [x.__dict__ for x in inventory],
        "chains": [x.__dict__ for x in chains],
        "chainStates": chain_states,
        "delegationPosture": classify_delegation_posture(chain_states),
        "blockedChains": sorted(k for k, v in chain_states.items() if v == "RECURSIVE_DELEGATION_BLOCKED"),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
