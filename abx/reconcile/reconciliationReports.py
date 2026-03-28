from __future__ import annotations

from abx.reconcile.reconciliationRecords import build_reconciliation_records, build_repair_legitimacy_records
from abx.reconcile.repairClassification import classify_repair
from abx.reconcile.types import AuthoritativeSourceRecord, ReconciliationGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_authoritative_source_records() -> list[AuthoritativeSourceRecord]:
    return [
        AuthoritativeSourceRecord("auth.001", "conf.001", "AUTHORITATIVE_SOURCE_SELECTED", "canonical_store"),
        AuthoritativeSourceRecord("auth.002", "conf.002", "AUTHORITATIVE_SOURCE_SELECTED", "canonical_store"),
        AuthoritativeSourceRecord("auth.003", "conf.003", "AUTHORITATIVE_SOURCE_SELECTED", "canonical_entity_map"),
        AuthoritativeSourceRecord("auth.004", "conf.004", "AUTHORITATIVE_SOURCE_SELECTED", "schema_registry"),
        AuthoritativeSourceRecord("auth.005", "conf.005", "AUTHORITATIVE_SOURCE_SELECTED", "replay_ledger"),
        AuthoritativeSourceRecord("auth.006", "conf.006", "AUTHORITATIVE_SOURCE_SELECTED", "policy_steward"),
        AuthoritativeSourceRecord("auth.007", "conf.007", "AUTHORITATIVE_SOURCE_SELECTED", "backend_truth"),
        AuthoritativeSourceRecord("auth.008", "conf.008", "NOT_COMPUTABLE", "unknown"),
        AuthoritativeSourceRecord("auth.009", "conf.009", "AUTHORITY_AMBIGUOUS", "unknown"),
        AuthoritativeSourceRecord("auth.010", "conf.010", "AUTHORITY_AMBIGUOUS", "pending_arbiter"),
    ]


def build_reconciliation_report() -> dict[str, object]:
    reconciliations = build_reconciliation_records()
    legitimacy = build_repair_legitimacy_records()
    authority = build_authoritative_source_records()
    legitimacy_idx = {x.reconciliation_ref: x for x in legitimacy}
    states = {
        x.reconciliation_id: classify_repair(
            repair_mode=x.repair_mode,
            reconciliation_state=x.reconciliation_state,
            legitimacy_state=legitimacy_idx[x.reconciliation_id].legitimacy_state,
        )
        for x in reconciliations
    }

    errors = []
    for row in reconciliations:
        state = states[row.reconciliation_id]
        if state in {"REPAIR_FORBIDDEN", "NOT_COMPUTABLE"}:
            errors.append(ReconciliationGovernanceErrorRecord("RECONCILIATION_BLOCKED", "ERROR", f"{row.conflict_ref} state={state}"))
        elif state in {"REPAIR_LEGITIMACY_UNKNOWN", "QUARANTINE_REPAIR"}:
            errors.append(ReconciliationGovernanceErrorRecord("RECONCILIATION_ATTENTION", "WARN", f"{row.conflict_ref} state={state}"))

    report = {
        "artifactType": "ReconciliationAudit.v1",
        "artifactId": "reconciliation-audit",
        "reconciliations": [x.__dict__ for x in reconciliations],
        "legitimacy": [x.__dict__ for x in legitimacy],
        "authoritativeSources": [x.__dict__ for x in authority],
        "reconciliationStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
