from __future__ import annotations

from abx.semantic.types import SchemaEvolutionRecord


def build_schema_evolution_inventory() -> tuple[SchemaEvolutionRecord, ...]:
    return (
        SchemaEvolutionRecord("evo.packet.v3-v4", "packet.schema", "v3", "v4", "STRUCTURALLY_COMPATIBLE", "SEMANTICALLY_COMPATIBLE"),
        SchemaEvolutionRecord(
            "evo.risk.v2-v3",
            "risk.schema",
            "v2",
            "v3",
            "STRUCTURALLY_COMPATIBLE",
            "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED",
        ),
        SchemaEvolutionRecord("evo.legacy.v1-v4", "legacy.schema", "v1", "v4", "ADAPTER_ONLY_COMPATIBLE", "MIGRATION_REQUIRED"),
        SchemaEvolutionRecord("evo.shadow.v0-v4", "shadow.schema", "v0", "v4", "NOT_COMPUTABLE", "NOT_COMPUTABLE"),
    )
