from __future__ import annotations

import json
from pathlib import Path

from webpanel.operator_console import _classify_pipeline_final_result, _pipeline_map_projection


def test_rune_execution_artifact_phase_enum_includes_closure_phases() -> None:
    schema_path = Path("aal_core/schemas/rune_execution_artifact.v1.json")
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    phase_enum = payload["properties"]["phase"]["enum"]
    assert "AUDIT" in phase_enum
    assert "BINDING" in phase_enum
    assert "CONTEXT_RESTORE" in phase_enum


def test_pipeline_map_projection_is_not_computable_without_callable_payload() -> None:
    parse_projection = {"status": "SUCCESS", "artifact_ref": "x"}
    result = _pipeline_map_projection(parse_projection=parse_projection, selected_run_id="run.test")
    assert result["status"] == "NOT_COMPUTABLE"
    assert result["reason"] == "map_callable_not_exposed"


def test_pipeline_map_projection_uses_callable_payload_when_present() -> None:
    parse_projection = {"status": "SUCCESS", "artifact_ref": "x"}
    map_payload = {"entities": ["entity_a", "entity_b"], "relations": ["a->b"], "artifact_ref": "map.artifact"}
    result = _pipeline_map_projection(
        parse_projection=parse_projection,
        selected_run_id="run.test",
        map_callable_payload=map_payload,
    )
    assert result["status"] == "SUCCESS"
    assert result["reason"] == ""
    assert result["artifact_ref"] == "map.artifact"
    assert result["map_context"]["relation_count"] == 1
    assert result["map_context"]["entities"] == ["entity_a", "entity_b"]


def test_pipeline_final_result_flags_projection_only_as_partial() -> None:
    result = _classify_pipeline_final_result(
        step_records=[
            {"step_name": "ingest", "status": "SUCCESS", "provenance": "pipeline.step.ingest.v3.4.adapter.run_compliance_probe"},
            {"step_name": "diff_validate", "status": "SUCCESS", "provenance": "pipeline.step.diff_validate.v3.4.adapter.run_execution_validator"},
            {"step_name": "review_audit", "status": "SUCCESS", "provenance": "pipeline.step.review_audit.v3.4.adapter.run_closure_audit"},
            {"step_name": "parse", "status": "SUCCESS", "provenance": "pipeline.step.parse.v3.5.projection"},
        ],
        artifact_paths=["a", "b", "c"],
        linkage={"ledger_record_ids": ["r1"], "ledger_artifact_ids": [], "correlation_pointers": []},
    )
    assert result["final_classification"] == "PARTIAL"
    assert result["overall_status_rule"] == "classification.synthetic_projection_detected"
