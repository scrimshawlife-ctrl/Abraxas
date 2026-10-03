from __future__ import annotations

from abx.evidence.types import ConflictingEvidenceRecord


def build_conflicting_evidence_records() -> tuple[ConflictingEvidenceRecord, ...]:
    return (
        ConflictingEvidenceRecord("conf.publish.001", "PUBLICATION_DECISION", "CONFLICTING_EVIDENCE", ("sig.a", "sig.b")),
        ConflictingEvidenceRecord("conf.override.001", "POLICY_EXCEPTION", "NO_CONFLICT", ("sig.c", "sig.c")),
    )
