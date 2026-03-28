from __future__ import annotations

from abx.explanation.compressionClassification import classify_compression
from abx.explanation.narrativeCompressionRecords import build_narrative_compression_records
from abx.explanation.types import ExplanationGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_narrative_compression_report() -> dict[str, object]:
    rows = build_narrative_compression_records()
    states = {x.compression_id: classify_compression(compression_state=x.compression_state, omitted_context=x.omitted_context) for x in rows}
    errors = []
    for row in rows:
        state = states[row.compression_id]
        if state in {"COMPRESSED_WITH_HIDDEN_LOSS_RISK", "COMPRESSION_UNSAFE"}:
            errors.append(ExplanationGovernanceErrorRecord("COMPRESSION_HIDDEN_LOSS", "ERROR", f"{row.surface_ref} state={state}"))
        elif state in {"COMPRESSED_WITH_NOTED_LOSS", "NOT_COMPUTABLE"}:
            errors.append(ExplanationGovernanceErrorRecord("COMPRESSION_ATTENTION_REQUIRED", "WARN", f"{row.surface_ref} state={state}"))
    report = {
        "artifactType": "NarrativeCompressionAudit.v1",
        "artifactId": "narrative-compression-audit",
        "compression": [x.__dict__ for x in rows],
        "compressionStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
