from __future__ import annotations

from webpanel.operator_console import (
    _ABRAXAS_PIPELINE_REVIEW_PATH_ID,
    _bounded_list_or_none,
    _build_pipeline_suitability_summary,
    _dedupe_preserve_order,
    _derive_abraxas_synthesis_output,
    _derive_anomaly_gap_detector,
    _derive_detector_fusion_output,
    _derive_pressure_friction_detector,
    _derive_routing_recommendation_reason,
    _compose_manual_override_surface,
    _resolve_manual_pipeline_override,
    _derive_signal_sufficiency_surface,
    _derive_fusion_input_surface,
    build_view_state,
    _render_compare,
    _render_trace,
)


def test_dedupe_preserve_order_is_stable_and_bounded():
    values = ["a", "b", "a", "", "c", "b", "d"]
    assert _dedupe_preserve_order(values, limit=3) == ["a", "b", "c"]


def test_bounded_list_or_none_returns_none_token_when_empty():
    assert _bounded_list_or_none([], limit=3) == ["none"]
    assert _bounded_list_or_none(["", "  "], limit=3) == ["none"]


def test_pressure_detector_summary_distinguishes_mildly_degraded_band():
    out = _derive_pressure_friction_detector(
        structural_signals={
            "missing_field_count": 1,
            "blocked_or_not_computable_count": 0,
            "degraded_step_count": 0,
            "relation_count": 2,
            "entity_count": 2,
            "transition_count": 1,
        },
        selected_run_id="run-1",
    )
    assert out["pressure_label"] == "MODERATE"
    assert "condition=mildly_degraded" in out["detector_summary"]


def test_anomaly_detector_summary_distinguishes_minor_vs_broken_gap():
    minor = _derive_anomaly_gap_detector(
        anomaly_gap_signals={
            "missing_artifact_count": 1,
            "missing_linkage_count": 0,
            "empty_required_field_count": 0,
            "broken_expected_step_pattern_count": 0,
            "review_export_mismatch_count": 0,
            "unexpected_not_computable_count": 0,
        },
        selected_run_id="run-1",
    )
    major = _derive_anomaly_gap_detector(
        anomaly_gap_signals={
            "missing_artifact_count": 1,
            "missing_linkage_count": 1,
            "empty_required_field_count": 0,
            "broken_expected_step_pattern_count": 2,
            "review_export_mismatch_count": 0,
            "unexpected_not_computable_count": 0,
        },
        selected_run_id="run-1",
    )
    assert minor["gap_label"] == "INCOMPLETE"
    assert "gap_state=minor_anomaly" in minor["detector_summary"]
    assert major["gap_label"] == "BROKEN"
    assert "gap_state=broken_gap" in major["detector_summary"]


def test_synthesis_dedupes_reasons_and_blockers_and_sets_actionable_next_step():
    out = _derive_abraxas_synthesis_output(
        synthesis_input_surface={
            "pipeline_status": "SUCCESS",
            "pipeline_final_state": {
                "pipeline_final_status": "SUCCESS",
                "pipeline_status_resolved": True,
            },
            "fusion_label": "BROKEN_SIGNAL",
            "fusion_status": "SUCCESS",
            "signal_sufficiency_status": "SUFFICIENT",
            "governance_policy_mode": "decision_review",
            "runtime_outcome_status": "FAILED",
            "runtime_blocker_summary": ["map:artifact_missing", "map:artifact_missing"],
        },
        selected_run_id="run-1",
    )
    assert out["synthesis_label"] == "BLOCKED"
    assert out["synthesis_blockers"] == ["map:artifact_missing"]
    assert out["synthesis_reasons"] == ["runtime_blockers_dominate_pipeline_success"]
    assert "Resolve the first runtime blocker" in out["synthesis_next_step"]


def test_routing_reason_distinguishes_review_ready_and_less_blocked():
    review_reason = _derive_routing_recommendation_reason(
        review_context=True,
        recommended_pipeline_id=_ABRAXAS_PIPELINE_REVIEW_PATH_ID,
        top_classification="NOT_COMPUTABLE",
        top_blocking_reason="none",
    )
    ready_reason = _derive_routing_recommendation_reason(
        review_context=False,
        recommended_pipeline_id="ABRAXAS.PIPELINE.v1",
        top_classification="SUCCESS",
        top_blocking_reason="none",
    )
    less_blocked_reason = _derive_routing_recommendation_reason(
        review_context=False,
        recommended_pipeline_id="ABRAXAS.PIPELINE.v1",
        top_classification="NOT_COMPUTABLE",
        top_blocking_reason="none",
    )

    assert review_reason == "review_preferred_due_to_review_context_and_eligibility"
    assert ready_reason == "ready_preferred_due_to_higher_readiness"
    assert less_blocked_reason == "less_blocked_preferred_due_to_clear_gating"


def test_manual_override_resolution_explicit_for_not_requested_applied_and_rejected():
    none_requested = _resolve_manual_pipeline_override(
        manual_pipeline_override=None,
        canonical_pipeline_ids=["ABRAXAS.PIPELINE.v1", _ABRAXAS_PIPELINE_REVIEW_PATH_ID],
    )
    applied = _resolve_manual_pipeline_override(
        manual_pipeline_override=_ABRAXAS_PIPELINE_REVIEW_PATH_ID,
        canonical_pipeline_ids=["ABRAXAS.PIPELINE.v1", _ABRAXAS_PIPELINE_REVIEW_PATH_ID],
    )
    rejected = _resolve_manual_pipeline_override(
        manual_pipeline_override="ABRAXAS.PIPELINE.unknown",
        canonical_pipeline_ids=["ABRAXAS.PIPELINE.v1", _ABRAXAS_PIPELINE_REVIEW_PATH_ID],
    )

    assert none_requested["manual_override_status"] == "not_requested"
    assert applied["manual_override_status"] == "applied"
    assert applied["manual_override_applied"] == _ABRAXAS_PIPELINE_REVIEW_PATH_ID
    assert rejected["manual_override_status"] == "rejected_unknown_pipeline"
    assert rejected["attempted_override"] == "ABRAXAS.PIPELINE.unknown"
    assert "manual override rejected" in rejected["manual_override_message"]


def test_manual_override_resolution_trims_input_before_registry_match():
    applied = _resolve_manual_pipeline_override(
        manual_pipeline_override=f"  {_ABRAXAS_PIPELINE_REVIEW_PATH_ID}  ",
        canonical_pipeline_ids=["ABRAXAS.PIPELINE.v1", _ABRAXAS_PIPELINE_REVIEW_PATH_ID],
    )
    assert applied["manual_override_status"] == "applied"
    assert applied["attempted_override"] == _ABRAXAS_PIPELINE_REVIEW_PATH_ID


def test_compose_manual_override_surface_enforces_stable_keys_and_defaults():
    surface = _compose_manual_override_surface(
        manual_override_resolution={
            "attempted_override": "  ABRAXAS.PIPELINE.unknown  ",
            "manual_override_applied": "",
            "manual_override_status": "",
            "manual_override_message": "",
        }
    )
    assert surface == {
        "attempted_pipeline_override": "ABRAXAS.PIPELINE.unknown",
        "manual_pipeline_override": "",
        "manual_override_status": "not_requested",
        "manual_override_message": "manual override not requested: using deterministic recommendation",
    }


def test_view_state_routing_surfaces_include_rejected_override_contract(tmp_path):
    view = build_view_state(
        base_dir=tmp_path,
        manual_pipeline_override="ABRAXAS.PIPELINE.unknown",
    )
    assert view.pipeline_routing["manual_override_status"] == "rejected_unknown_pipeline"
    assert view.pipeline_routing["attempted_pipeline_override"] == "ABRAXAS.PIPELINE.unknown"
    assert view.pipeline_routing["pipeline_routing_workspace_payload"]["manual_override_status"] == "rejected_unknown_pipeline"
    assert view.pipeline_routing["pipeline_routing_workspace_payload"]["attempted_pipeline_override"] == "ABRAXAS.PIPELINE.unknown"
    assert view.pipeline_routing["routing_export_preview"]["manual_override_status"] == "rejected_unknown_pipeline"
    assert view.pipeline_routing["routing_export_preview"]["attempted_pipeline_override"] == "ABRAXAS.PIPELINE.unknown"


def test_signal_sufficiency_minimal_signal_is_insufficient():
    suff = _derive_signal_sufficiency_surface(
        selected_run_id="run-1",
        structural_signals={"entity_count": 0, "relation_count": 0, "transition_count": 0},
        pressure_friction_detector={"detector_status": "SUCCESS"},
        motif_recurrence_detector={"detector_status": "SUCCESS"},
        instability_drift_detector={"detector_status": "SUCCESS"},
        anomaly_gap_detector={"detector_status": "SUCCESS", "gap_label": "COMPLETE", "anomaly_label": "NONE"},
        not_computable_subcodes=[],
        binding_health_surface={"detector_ready_state": "READY"},
    )
    assert suff["signal_sufficiency_status"] == "THIN"
    assert "minimal_structural_richness" in suff["signal_sufficiency_reasons"]


def test_fusion_uses_compressed_reason_not_raw_label_echo():
    pressure = {"detector_status": "SUCCESS", "pressure_label": "LOW", "friction_label": "CLEAR", "pressure_reasons": []}
    motif = {"detector_status": "SUCCESS", "motif_label": "SPARSE", "recurrence_label": "NONE", "motif_reasons": []}
    drift = {"detector_status": "SUCCESS", "instability_label": "STABLE", "drift_label": "NONE", "drift_reasons": []}
    anomaly = {"detector_status": "SUCCESS", "anomaly_label": "NONE", "gap_label": "COMPLETE", "anomaly_reasons": []}
    fusion_input = _derive_fusion_input_surface(
        structural_signals={"entity_count": 3, "relation_count": 2, "transition_count": 1},
        pressure_friction_detector=pressure,
        motif_recurrence_detector=motif,
        instability_drift_detector=drift,
        anomaly_gap_detector=anomaly,
    )
    out = _derive_detector_fusion_output(
        selected_run_id="run-1",
        fusion_input_surface=fusion_input,
        pressure_friction_detector=pressure,
        motif_recurrence_detector=motif,
        instability_drift_detector=drift,
        anomaly_gap_detector=anomaly,
        signal_sufficiency_surface={"signal_sufficiency_status": "SUFFICIENT"},
    )
    assert out["compressed_fusion_reason"] == "stable_pattern_across_detector_families"
    assert all("label=" not in token for token in out["fused_reasons"])


def test_suitability_summary_is_legible_and_bounded():
    summary = _build_pipeline_suitability_summary(
        allowlisted="true",
        invokable="true",
        required_context_present=True,
        final_classification="SUCCESS",
        blocking_reason="none",
    )
    assert "eligibility allowlisted=true" in summary
    assert "classification=SUCCESS" in summary


def test_trace_render_summary_line_is_readable():
    rendered = _render_trace(
        {
            "recent_activity": [{"x": 1}, {"x": 2}],
            "recent_decisions": [{"x": 1}],
            "execution_ledger_slice": [{"x": 1}, {"x": 2}, {"x": 3}],
        }
    )
    assert rendered["summary_line"] == "Trace density: activity=2; decisions=1; ledger=3"


def test_compare_render_summary_line_present_for_enabled_and_disabled():
    disabled = _render_compare({"enabled": False, "reason": "no_comparison_context"})
    enabled = _render_compare({"enabled": True, "reason": "comparison_available"})
    assert disabled["summary_line"] == "Compare unavailable: no comparison context."
    assert enabled["summary_line"] == "Compare ready: selected and comparison runs are available."
