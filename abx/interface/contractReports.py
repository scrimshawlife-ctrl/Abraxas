from __future__ import annotations

from abx.interface.contractClassification import classify_contract
from abx.interface.interfaceContractRecords import build_interface_contract_records
from abx.interface.types import InterfaceGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_interface_contract_report() -> dict[str, object]:
    rows = build_interface_contract_records()
    states = {x.contract_id: classify_contract(contract_state=x.contract_state, integrity_surface=x.integrity_surface) for x in rows}
    errors = []
    for row in rows:
        state = states[row.contract_id]
        if state in {"CONTRACT_BROKEN", "NOT_COMPUTABLE"}:
            errors.append(InterfaceGovernanceErrorRecord("CONTRACT_BLOCKING", "ERROR", f"{row.boundary_ref} state={state}"))
        elif state in {"CONTRACT_DRIFT_SUSPECTED"}:
            errors.append(InterfaceGovernanceErrorRecord("CONTRACT_ATTENTION", "WARN", f"{row.boundary_ref} state={state}"))
    report = {
        "artifactType": "InterfaceContractAudit.v1",
        "artifactId": "interface-contract-audit",
        "contracts": [x.__dict__ for x in rows],
        "contractStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
