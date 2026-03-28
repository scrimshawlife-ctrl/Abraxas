from __future__ import annotations

from abx.tradeoff.sacrificeClassification import classify_tradeoff
from abx.tradeoff.tradeoffRecords import build_objective_conflict_records, build_sacrifice_records, build_tradeoff_records
from abx.tradeoff.types import TradeoffGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_tradeoff_legibility_report() -> dict[str, object]:
    tradeoff = build_tradeoff_records()
    sacrifice = build_sacrifice_records()
    conflicts = build_objective_conflict_records()
    sacrifice_by_ref = {x.decision_ref: x for x in sacrifice}
    conflict_by_ref = {x.decision_ref: x for x in conflicts}

    states = {}
    for row in tradeoff:
        sacrifice_row = sacrifice_by_ref.get(row.decision_ref)
        conflict_row = conflict_by_ref.get(row.decision_ref)
        states[row.tradeoff_id] = classify_tradeoff(
            tradeoff_state=row.tradeoff_state,
            sacrifice_state=sacrifice_row.sacrifice_state if sacrifice_row else "NOT_COMPUTABLE",
            resolution_state=conflict_row.resolution_state if conflict_row else "NOT_COMPUTABLE",
        )

    errors = []
    for row in tradeoff:
        state = states[row.tradeoff_id]
        if state in {"TRADEOFF_HIDDEN", "DOMINATION_SELECTED"}:
            errors.append(TradeoffGovernanceErrorRecord("TRADEOFF_LEGIBILITY_FAIL", "ERROR", f"{row.decision_ref} state={state}"))
        elif state in {"COMPROMISE_SELECTED", "NOT_COMPUTABLE"}:
            errors.append(TradeoffGovernanceErrorRecord("TRADEOFF_ATTENTION_REQUIRED", "WARN", f"{row.decision_ref} state={state}"))

    report = {
        "artifactType": "TradeoffLegibilityAudit.v1",
        "artifactId": "tradeoff-legibility-audit",
        "tradeoff": [x.__dict__ for x in tradeoff],
        "sacrifice": [x.__dict__ for x in sacrifice],
        "conflicts": [x.__dict__ for x in conflicts],
        "tradeoffStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
