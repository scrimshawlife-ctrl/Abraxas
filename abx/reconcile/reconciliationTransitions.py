from __future__ import annotations

from abx.reconcile.types import ConsistencyTransitionRecord


def build_reconciliation_transition_records() -> list[ConsistencyTransitionRecord]:
    return [
        ConsistencyTransitionRecord("trn.001", "rec.001", "CONFLICT_DETECTED", "DURABLE_RESTORED", "refresh aligned with canonical ledger"),
        ConsistencyTransitionRecord("trn.002", "rec.002", "CONFLICT_DETECTED", "PROVISIONAL_RESTORED", "freshness restored pending decay validation"),
        ConsistencyTransitionRecord("trn.003", "rec.003", "CONFLICT_DETECTED", "PARTIAL_RESTORED", "identity merge left duplicate suspicion"),
        ConsistencyTransitionRecord("trn.004", "rec.004", "CONFLICT_DETECTED", "DURABLE_RESTORED", "rollback restored semantic compatibility"),
        ConsistencyTransitionRecord("trn.005", "rec.005", "CONFLICT_DETECTED", "DURABLE_RESTORED", "rebuild restored replayable lineage"),
        ConsistencyTransitionRecord("trn.006", "rec.006", "CONFLICT_DETECTED", "DURABLE_RESTORED", "authoritative overwrite approved and completed"),
        ConsistencyTransitionRecord("trn.007", "rec.007", "CONFLICT_DETECTED", "COSMETIC_ALIGNMENT_ACTIVE", "UI aligned but backend untouched"),
        ConsistencyTransitionRecord("trn.008", "rec.008", "CONFLICT_DETECTED", "NOT_COMPUTABLE", "repair legitimacy unresolved"),
        ConsistencyTransitionRecord("trn.009", "rec.009", "CONFLICT_DETECTED", "UNRESOLVED_CONFLICT_ACTIVE", "forbidden repair path retained"),
        ConsistencyTransitionRecord("trn.010", "rec.010", "CONFLICT_DETECTED", "VALIDATION_REQUIRED", "authority arbitration not finalized"),
    ]
