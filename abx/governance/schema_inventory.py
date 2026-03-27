from __future__ import annotations

from pathlib import Path

from abx.governance.types import CanonicalSchemaRecord, SchemaMappingRecord


def build_schema_inventory() -> list[CanonicalSchemaRecord]:
    rows = [
        CanonicalSchemaRecord(
            schema_id="schema.resonance_frame.v1",
            module_path="abx/resonance_frame.py",
            artifact_type="ResonanceFrame.v1",
            classification="CANONICAL",
            authority_level="authoritative",
            notes="Unified runtime frame for operator and governance truth surfaces.",
        ),
        CanonicalSchemaRecord(
            schema_id="schema.proof_chain.v1",
            module_path="abx/proof_chain.py",
            artifact_type="ProofChainArtifact.v1",
            classification="CANONICAL",
            authority_level="authoritative",
            notes="Deterministic reconstructability and lineage chain summary.",
        ),
        CanonicalSchemaRecord(
            schema_id="schema.closure_summary.v1",
            module_path="abx/closure_summary.py",
            artifact_type="ClosureSummaryArtifact.v1",
            classification="CANONICAL",
            authority_level="authoritative",
            notes="Run closure evidence snapshot for release gating.",
        ),
        CanonicalSchemaRecord(
            schema_id="schema.promotion_pack.v1",
            module_path="abx/promotion_pack.py",
            artifact_type="PromotionPackArtifact.v1",
            classification="CANONICAL",
            authority_level="authoritative",
            notes="Lifecycle promotion decision envelope.",
        ),
        CanonicalSchemaRecord(
            schema_id="schema.continuity_summary.v1",
            module_path="abx/continuity.py",
            artifact_type="ContinuitySummaryArtifact.v1",
            classification="CANONICAL",
            authority_level="authoritative",
            notes="Cross-run continuity and carry-forward legibility.",
        ),
        CanonicalSchemaRecord(
            schema_id="schema.frame_projection.v1",
            module_path="abx/resonance_frame.py",
            artifact_type="FrameProjection.v1",
            classification="ADAPTED",
            authority_level="derived",
            notes="Derived projection for operator readability; never authoritative.",
        ),
        CanonicalSchemaRecord(
            schema_id="schema.adapter_audit.v1",
            module_path="abx/frame_adapters.py",
            artifact_type="AdapterAuditArtifact.v1",
            classification="ADAPTED",
            authority_level="derived",
            notes="Adapter inventory report derived from assembly map.",
        ),
        CanonicalSchemaRecord(
            schema_id="schema.portfolio_view.v1",
            module_path="abx/operator_console.py",
            artifact_type="portfolio-view",
            classification="DEPRECATED_CANDIDATE",
            authority_level="derived",
            notes="Projection from simulation result, not a source-of-truth schema.",
        ),
        CanonicalSchemaRecord(
            schema_id="schema.raw_operator_stdout",
            module_path="abx/operator_console.py",
            artifact_type="raw-operator-stdout",
            classification="LEGACY",
            authority_level="legacy",
            notes="Debug surface kept for operational diagnosis only.",
        ),
    ]
    return sorted(rows, key=lambda x: x.schema_id)


def build_schema_mappings() -> list[SchemaMappingRecord]:
    mappings = [
        SchemaMappingRecord(
            mapping_id="mapping.runtime_identifiers",
            canonical_schema_id="schema.resonance_frame.v1",
            alias_surface="simulation/result identifiers",
            field_mappings=[("runId", "run_id"), ("scenarioId", "scenario_id")],
            status="ACTIVE",
        ),
        SchemaMappingRecord(
            mapping_id="mapping.status_signals",
            canonical_schema_id="schema.resonance_frame.v1",
            alias_surface="proof/validation/closure status names",
            field_mappings=[
                ("proof_status", "proof_chain_status"),
                ("validation_status", "validation_status"),
                ("closure_status", "closure_status"),
            ],
            status="ACTIVE",
        ),
        SchemaMappingRecord(
            mapping_id="mapping.portfolio_fields",
            canonical_schema_id="schema.resonance_frame.v1",
            alias_surface="operator portfolio inspector",
            field_mappings=[("equity", "portfolio.equity"), ("realizedPnl", "portfolio.realized_pnl")],
            status="DEPRECATED_CANDIDATE",
        ),
    ]
    return sorted(mappings, key=lambda x: x.mapping_id)


def schema_inventory_report() -> dict[str, object]:
    inventory = build_schema_inventory()
    mappings = build_schema_mappings()

    by_class: dict[str, int] = {}
    for row in inventory:
        by_class[row.classification] = by_class.get(row.classification, 0) + 1

    return {
        "artifactType": "SchemaInventoryArtifact.v1",
        "artifactId": "schema-inventory-abx",
        "root": Path(".").as_posix(),
        "classificationCounts": {k: by_class[k] for k in sorted(by_class)},
        "canonicalSchemas": [row.__dict__ for row in inventory],
        "mappings": [
            m.__dict__ | {"field_mappings": [{"from": src, "to": dst} for src, dst in m.field_mappings]}
            for m in mappings
        ],
    }
