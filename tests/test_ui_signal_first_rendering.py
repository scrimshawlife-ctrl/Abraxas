from __future__ import annotations

from webpanel.oracle_output import build_oracle_view
from webpanel.ui_signal_sections import REQUIRED_SIGNAL_SECTION_ORDER, normalize_signal_sections


def test_ui_renders_raw_signal_first():
    normalized = normalize_signal_sections(
        {
            "raw_signal": {"run_id": "run-1"},
            "structural_model": {"legacy_summary": "legacy"},
            "optional_lenses": {"fusion": "stable"},
            "claim_status": {"label": "READY", "status": "SUCCESS"},
            "omissions": [],
        }
    )
    assert list(normalized.keys()) == REQUIRED_SIGNAL_SECTION_ORDER


def test_ui_legacy_payload_maps_summary_to_structural_model():
    oracle_view = build_oracle_view(
        {
            "signal_id": "sig-1",
            "tier": "psychonaut",
            "lane": "canon",
            "indicators": {"score": 0.5},
            "evidence": ["ev-1"],
            "flags": {"suppressed": False},
            "provenance": {},
        }
    )
    legacy_summary = oracle_view["structured_signal_payload"]["structural_model"].get("legacy_summary", "")
    assert legacy_summary.startswith("Indicators:")


def test_ui_optional_lenses_do_not_replace_raw_signal():
    normalized = normalize_signal_sections(
        {
            "raw_signal": {"run_id": "run-visible"},
            "structural_model": {},
            "optional_lenses": {"legacy_blob": "available"},
            "claim_status": {"label": "ACTIVE", "status": "SUCCESS"},
            "omissions": [],
        }
    )
    assert normalized["raw_signal"]["run_id"] == "run-visible"
    assert normalized["optional_lenses"]["legacy_blob"] == "available"


def test_ui_renders_omissions_structurally():
    normalized = normalize_signal_sections(
        {
            "raw_signal": {"run_id": "run-2"},
            "structural_model": {},
            "optional_lenses": {},
            "claim_status": {"label": "BLOCKED", "status": "SUCCESS"},
            "omissions": [
                {
                    "omitted_by": "operator_console.abraxas_synthesis",
                    "omitted_reason": "pipeline_or_fusion_not_computable",
                    "boundary_type": "hard_boundary",
                    "source_pointer": "synthesis_input_surface.pipeline_unresolved_subcode",
                }
            ],
        }
    )
    assert normalized["omissions"][0]["omitted_by"] == "operator_console.abraxas_synthesis"
    assert normalized["omissions"][0]["omitted_reason"] == "pipeline_or_fusion_not_computable"
    assert normalized["omissions"][0]["boundary_type"] == "hard_boundary"
    assert normalized["omissions"][0]["source_pointer"] == "synthesis_input_surface.pipeline_unresolved_subcode"


def test_ui_does_not_generate_internal_redacted_placeholder():
    normalized = normalize_signal_sections(
        {
            "raw_signal": {"run_id": "run-3"},
            "structural_model": {},
            "optional_lenses": {},
            "claim_status": {"label": "VISIBLE", "status": "SUCCESS"},
            "omissions": [],
        }
    )
    assert "[redacted]" not in str(normalized).lower()


def test_ui_claim_status_metadata_is_visible():
    normalized = normalize_signal_sections(
        {
            "raw_signal": {"run_id": "run-4"},
            "structural_model": {},
            "optional_lenses": {},
            "claim_status": {"label": "READY", "status": "SUCCESS", "reasons": ["stable"]},
            "omissions": [],
        }
    )
    assert normalized["claim_status"]["label"] == "READY"
    assert normalized["claim_status"]["status"] == "SUCCESS"
