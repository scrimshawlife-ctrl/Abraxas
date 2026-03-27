from __future__ import annotations

from abraxas.runes.operators.no_causal_assert import apply_no_causal_assert
from abraxas.runes.operators.no_domain_prior import apply_no_domain_prior
from abraxas.runes.operators.provenance_seal import apply_provenance_seal
from abraxas.runes.operators.temporal_normalize import apply_temporal_normalize
from abraxas.runes.operators.tvm_frame import apply_tvm_frame
from abraxas.runes.operators.source_discover import apply_source_discover
from abraxas.runes.operators.source_resolve import apply_source_resolve
from abraxas.runes.operators.source_redundancy_check import apply_source_redundancy_check
from abraxas.runes.operators.metric_extract import apply_metric_extract
from abraxas.runes.operators.linguistic_source_discover import apply_linguistic_source_discover
from abraxas.runes.operators.synchronicity_map import apply_synchronicity_map
from abraxas.runes.operators.cohesion_score import apply_cohesion_score
from abraxas.runes.operators.influence_detect import apply_influence_detect
from abraxas.runes.operators.influence_weight import apply_influence_weight
from abraxas.runes.operators.rfa import apply_rfa
from abraxas.runes.operators.tam import apply_tam
from abraxas.runes.operators.wsss import apply_wsss
from abraxas.runes.operators.acquisition_layer import (
    apply_acquire_bulk,
    apply_acquire_cache_only,
    apply_acquire_surgical,
)


def test_no_causal_assert_strict_missing_payload_returns_not_computable() -> None:
    out = apply_no_causal_assert(None, strict_execution=True)
    assert out["compliance"] is False
    assert out["not_computable_detail"]["reason_code"] == "missing_payload"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_no_domain_prior_strict_missing_payload_returns_not_computable() -> None:
    out = apply_no_domain_prior(None, strict_execution=True)
    assert out["compliance"] is False
    assert out["not_computable_detail"]["reason_code"] == "missing_payload"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_provenance_seal_strict_missing_payload_returns_not_computable() -> None:
    out = apply_provenance_seal(None, strict_execution=True)
    assert out["payload_hash"] == ""
    assert out["not_computable_detail"]["reason_code"] == "missing_payload"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_temporal_normalize_strict_missing_timestamp_returns_not_computable() -> None:
    out = apply_temporal_normalize("", strict_execution=True)
    assert out["normalized_timestamp_utc"] == ""
    assert out["not_computable_detail"]["reason_code"] == "missing_timestamp"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_tvm_frame_strict_missing_metrics_returns_not_computable() -> None:
    out = apply_tvm_frame(None, window_start_utc="2025-01-01T00:00:00Z", window_end_utc="2025-01-01T01:00:00Z", strict_execution=True)
    assert out["frames"] == []
    assert out["not_computable_detail"]["reason_code"] == "missing_metrics"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_source_discover_strict_missing_inputs_returns_not_computable() -> None:
    out = apply_source_discover(strict_execution=True)
    assert out["candidates"] == []
    assert out["not_computable_detail"]["reason_code"] == "missing_signal_inputs"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_source_resolve_strict_missing_ids_returns_not_computable() -> None:
    out = apply_source_resolve(None, strict_execution=True)
    assert out["sources"] == []
    assert out["not_computable_detail"]["reason_code"] == "missing_source_ids"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_source_redundancy_check_strict_missing_sources_returns_not_computable() -> None:
    out = apply_source_redundancy_check(None, strict_execution=True)
    assert out["overlaps"] == []
    assert out["not_computable_detail"]["reason_code"] == "missing_sources"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_metric_extract_strict_missing_packets_returns_not_computable() -> None:
    out = apply_metric_extract(None, strict_execution=True)
    assert out["metrics"] == []
    assert out["not_computable_detail"]["reason_code"] == "missing_packets"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_linguistic_source_discover_strict_missing_tokens_returns_not_computable() -> None:
    out = apply_linguistic_source_discover(None, strict_execution=True)
    assert out["candidates"] == []
    assert out["not_computable_detail"]["reason_code"] == "missing_tokens"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_synchronicity_map_strict_missing_frames_returns_not_computable() -> None:
    out = apply_synchronicity_map(None, strict_execution=True)
    assert out["envelopes"] == []
    assert out["not_computable_detail"]["reason_code"] == "missing_frames"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_cohesion_score_strict_missing_envelopes_returns_not_computable() -> None:
    out = apply_cohesion_score(None, strict_execution=True)
    assert out["not_computable"] is True
    assert out["not_computable_detail"]["reason_code"] == "missing_synchronicity_envelopes"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_influence_detect_strict_missing_frames_returns_not_computable() -> None:
    out = apply_influence_detect(None, strict_execution=True)
    assert "_global" in out["ics"]
    assert out["not_computable_detail"]["reason_code"] == "missing_frames"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_influence_weight_strict_missing_bundle_returns_not_computable() -> None:
    out = apply_influence_weight(None, strict_execution=True)
    assert out["weights"] == {}
    assert out["not_computable_detail"]["reason_code"] == "missing_ics_bundle"
    assert out["not_computable_detail"]["strict_execution"] is True


def test_rfa_strict_missing_inputs_returns_not_computable() -> None:
    out = apply_rfa(None, None, None, strict_execution=True)
    assert out["anchored_field"] == {}
    assert out["not_computable"]["reason_code"] == "missing_rfa_inputs"
    assert out["not_computable"]["strict_execution"] is True


def test_tam_strict_missing_inputs_returns_not_computable() -> None:
    out = apply_tam(None, None, None, strict_execution=True)
    assert out["semantic_trace"] == []
    assert out["not_computable"]["reason_code"] == "missing_tam_inputs"
    assert out["not_computable"]["strict_execution"] is True


def test_wsss_strict_missing_inputs_returns_not_computable() -> None:
    out = apply_wsss(None, None, None, strict_execution=True)
    assert out["validation_result"] == "not_computable"
    assert out["not_computable"]["reason_code"] == "missing_wsss_inputs"
    assert out["not_computable"]["strict_execution"] is True


def test_acquire_bulk_strict_returns_not_computable() -> None:
    out = apply_acquire_bulk(
        source_id="TEST",
        window_utc="2026-01-01T00:00:00Z",
        params={},
        run_ctx={"run_id": "TEST_RUN"},
        strict_execution=True,
    )
    assert out["raw_path"] == ""
    assert out["not_computable"]["reason_code"] == "adapter_integration_required"


def test_acquire_cache_only_strict_returns_not_computable() -> None:
    out = apply_acquire_cache_only(
        cache_keys=["k1", "k2"],
        run_ctx={"run_id": "TEST_RUN"},
        strict_execution=True,
    )
    assert out["paths"] == []
    assert out["not_computable"]["reason_code"] == "cache_replay_strict_blocked"


def test_acquire_surgical_strict_returns_not_computable() -> None:
    out = apply_acquire_surgical(
        target="https://example.com",
        reason_code="BLOCKED",
        hard_cap_requests=3,
        run_ctx={"run_id": "TEST_RUN"},
        strict_execution=True,
    )
    assert out["manifest_candidates"] == []
    assert out["not_computable"]["reason_code"] == "surgical_adapter_integration_required"
