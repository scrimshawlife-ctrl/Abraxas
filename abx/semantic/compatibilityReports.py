from __future__ import annotations

from abx.semantic.compatibilityClassification import classify_compatibility
from abx.semantic.schemaEvolutionRecords import build_schema_evolution_records
from abx.semantic.types import CompatibilitySemanticRecord, SemanticGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_schema_evolution_report() -> dict[str, object]:
    rows = build_schema_evolution_records()
    compatibility = tuple(
        CompatibilitySemanticRecord(
            compatibility_id=f"comp.{x.evolution_id}",
            evolution_id=x.evolution_id,
            compatibility_state=classify_compatibility(
                structural_compatibility=x.structural_compatibility,
                semantic_compatibility=x.semantic_compatibility,
            ),
            adapter_state="ADAPTER_ONLY" if x.structural_compatibility == "ADAPTER_ONLY_COMPATIBLE" else "NATIVE",
            migration_required="YES" if x.semantic_compatibility in {"MIGRATION_REQUIRED", "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED"} else "NO",
        )
        for x in rows
    )
    errors = []
    for row in compatibility:
        if row.compatibility_state in {"BACKWARD_PARSEABLE_ONLY", "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED"}:
            errors.append(SemanticGovernanceErrorRecord("COMPATIBILITY_SEMANTIC_GAP", "WARN", f"{row.evolution_id} state={row.compatibility_state}"))
        if row.compatibility_state == "NOT_COMPUTABLE":
            errors.append(SemanticGovernanceErrorRecord("COMPATIBILITY_NOT_COMPUTABLE", "ERROR", f"{row.evolution_id} state=NOT_COMPUTABLE"))
    report = {
        "artifactType": "SchemaEvolutionAudit.v1",
        "artifactId": "schema-evolution-audit",
        "evolution": [x.__dict__ for x in rows],
        "compatibility": [x.__dict__ for x in compatibility],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
