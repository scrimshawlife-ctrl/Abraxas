from __future__ import annotations

from abx.explanation.compressionLossRecords import build_compression_loss_records
from abx.explanation.explanationTransitions import build_explanation_transition_records
from abx.explanation.omissionRiskRecords import build_transition_omission_records
from abx.explanation.types import ExplanationGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_explanation_transition_report() -> dict[str, object]:
    transitions = build_explanation_transition_records()
    losses = build_compression_loss_records()
    omission = build_transition_omission_records()

    errors = []
    for row in transitions:
        if row.to_state in {"BOUNDARY_BLOCK_ACTIVE", "CAUSAL_OVERREACH_ACTIVE"}:
            errors.append(ExplanationGovernanceErrorRecord("EXPLANATION_BOUNDARY_BLOCKED", "ERROR", f"{row.surface_ref} to={row.to_state}"))
        elif row.to_state in {"COMPRESSION_LOSS_ACTIVE", "CAVEAT_OMISSION_ACTIVE"}:
            errors.append(ExplanationGovernanceErrorRecord("EXPLANATION_REFRESH_REQUIRED", "WARN", f"{row.surface_ref} to={row.to_state}"))

    report = {
        "artifactType": "ExplanationTransitionAudit.v1",
        "artifactId": "explanation-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "compressionLoss": [x.__dict__ for x in losses],
        "omission": [x.__dict__ for x in omission],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
