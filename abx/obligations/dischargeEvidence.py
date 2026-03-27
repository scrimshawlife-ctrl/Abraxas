from __future__ import annotations

from abx.obligations.types import DischargeEvidenceRecord


def build_discharge_evidence_records() -> list[DischargeEvidenceRecord]:
    rows = [
        DischargeEvidenceRecord("evidence.release-v1-6", "commitment.release-v1-6", "PARTIALLY_DISCHARGED", "artifact.release.v1_6.rc"),
        DischargeEvidenceRecord("evidence.incident-followup", "commitment.incident-followup", "IN_PROGRESS", "artifact.incident.followup.thread"),
        DischargeEvidenceRecord("evidence.docs-refresh", "commitment.docs-refresh", "SCHEDULED", "artifact.docs.backlog"),
        DischargeEvidenceRecord("evidence.legacy-api-window", "commitment.legacy-api-window", "MISSED", "artifact.api.sunset.notice"),
        DischargeEvidenceRecord("evidence.deprecated-export", "commitment.deprecated-export", "WAIVED", "artifact.waiver.export"),
    ]
    return sorted(rows, key=lambda x: x.evidence_id)
