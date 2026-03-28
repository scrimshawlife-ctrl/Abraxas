from __future__ import annotations

from abx.explanation.explanationBoundaryRecords import build_explanation_boundary_records, build_explanation_layer_records
from abx.explanation.layerClassification import classify_layer
from abx.explanation.types import ExplanationGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_explanation_boundary_report() -> dict[str, object]:
    boundaries = build_explanation_boundary_records()
    layers = build_explanation_layer_records()
    boundary_by_surface = {x.surface_ref: x.boundary_state for x in boundaries}
    layer_states = {
        x.layer_id: classify_layer(layer_state=x.layer_state, boundary_state=boundary_by_surface.get(x.surface_ref, "BOUNDARY_AMBIGUOUS"))
        for x in layers
    }
    errors = []
    for row in boundaries:
        if row.boundary_state == "BOUNDARY_EXCEEDED":
            errors.append(ExplanationGovernanceErrorRecord("BOUNDARY_EXCEEDED", "ERROR", f"{row.surface_ref} exceeded"))
        elif row.boundary_state in {"BOUNDARY_AMBIGUOUS", "NOT_COMPUTABLE"}:
            errors.append(ExplanationGovernanceErrorRecord("BOUNDARY_ATTENTION_REQUIRED", "WARN", f"{row.surface_ref} state={row.boundary_state}"))
    report = {
        "artifactType": "ExplanationBoundaryAudit.v1",
        "artifactId": "explanation-boundary-audit",
        "boundaries": [x.__dict__ for x in boundaries],
        "layers": [x.__dict__ for x in layers],
        "layerStates": layer_states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
