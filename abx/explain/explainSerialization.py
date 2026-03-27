from __future__ import annotations

from abx.explain_ir import ExplainIR
from abx.observability.types import ExplainIRArtifact, ProvenancePartitionRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def to_observability_explain(ir: ExplainIR) -> tuple[ExplainIRArtifact, ProvenancePartitionRecord]:
    artifact = ExplainIRArtifact(
        artifact_id=f"explain-{sha256_bytes(dumps_stable(ir.model_dump()).encode('utf-8'))[:16]}",
        explain_rune_id=ir.explain_rune_id,
        event_type=ir.event_type,
        observed=list(ir.provenance.observed),
        inferred=list(ir.provenance.inferred),
        speculative=list(ir.provenance.speculative),
        confidence=float(ir.confidence),
    )
    partition = ProvenancePartitionRecord(
        artifact_id=artifact.artifact_id,
        observed_count=len(artifact.observed),
        inferred_count=len(artifact.inferred),
        speculative_count=len(artifact.speculative),
    )
    return artifact, partition


def serialize_explain_artifact(artifact: ExplainIRArtifact) -> str:
    return dumps_stable(artifact.__dict__)
