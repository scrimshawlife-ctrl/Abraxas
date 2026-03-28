from __future__ import annotations

from abx.lineage.derivationClassification import classify_derivation
from abx.lineage.provenanceRecords import build_provenance_records
from abx.lineage.types import DerivationRecord, LineageGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_provenance_report() -> dict[str, object]:
    rows = build_provenance_records()
    derivation = tuple(
        DerivationRecord(
            derivation_id=f"drv.{x.provenance_id}",
            provenance_id=x.provenance_id,
            derivation_state=classify_derivation(provenance_state=x.provenance_state, transform_chain=x.transform_chain),
            stale_state="YES" if x.provenance_state in {"PROVENANCE_STALE", "PROVENANCE_BROKEN"} else "NO",
            rederivation_required="YES" if x.provenance_state in {"PROVENANCE_STALE", "PROVENANCE_BROKEN", "NOT_COMPUTABLE"} else "NO",
        )
        for x in rows
    )
    errors = []
    for row in rows:
        if row.provenance_state in {"PROVENANCE_BROKEN", "NOT_COMPUTABLE"}:
            errors.append(
                LineageGovernanceErrorRecord(
                    code="PROVENANCE_BROKEN",
                    severity="ERROR",
                    message=f"{row.lineage_id} has {row.provenance_state}",
                )
            )
        elif row.provenance_state in {"PROVENANCE_PARTIAL", "PROVENANCE_STALE"}:
            errors.append(
                LineageGovernanceErrorRecord(
                    code="PROVENANCE_PARTIAL_OR_STALE",
                    severity="WARN",
                    message=f"{row.lineage_id} has {row.provenance_state}",
                )
            )
    report = {
        "artifactType": "ProvenanceAudit.v1",
        "artifactId": "provenance-audit",
        "provenance": [x.__dict__ for x in rows],
        "derivations": [x.__dict__ for x in derivation],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
