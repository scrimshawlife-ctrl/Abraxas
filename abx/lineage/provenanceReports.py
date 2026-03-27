from __future__ import annotations

from abx.lineage.derivationClassification import classify_derivation
from abx.lineage.provenanceRecords import build_provenance_records
from abx.lineage.types import DerivationRecord
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
        )
        for x in rows
    )
    report = {
        "artifactType": "ProvenanceAudit.v1",
        "artifactId": "provenance-audit",
        "provenance": [x.__dict__ for x in rows],
        "derivations": [x.__dict__ for x in derivation],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
