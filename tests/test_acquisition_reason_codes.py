from __future__ import annotations

from abraxas.acquisition.reason_codes import (
    CACHE_POLICY_MANIFEST_PROBE,
    CACHE_POLICY_OFFLINE_ONLY,
    BULK_FAILED,
    CACHE_FALLBACK_AFTER_BULK_FAILED,
    FETCH_FAILED,
    DECODO_USED,
    UNKNOWN_POLICY_REASON,
    canonicalize_policy_reason,
    POLICY_CACHE_ONLY,
    SURGICAL_FAILED,
    classify_reason_code,
    derive_manifest_reason_code,
    format_bulk_failed_reason,
    format_cache_fallback_reason,
    format_surgical_failed_reason,
    summarize_reason_codes,
    summarize_policy_reasons,
    validate_cache_policy_reason,
)


def test_derive_manifest_reason_code_policy_cache_only() -> None:
    reason = derive_manifest_reason_code(["policy_cache_only_cache_hit", "policy_cache_only_cache_miss"])
    assert reason == POLICY_CACHE_ONLY


def test_derive_manifest_reason_code_prefers_failure_classes() -> None:
    assert derive_manifest_reason_code(["bulk_failed:TimeoutError"]) == BULK_FAILED
    assert derive_manifest_reason_code(["surgical_failed:ValueError:bulk_failed:TimeoutError"]) == SURGICAL_FAILED


def test_derive_manifest_reason_code_detects_cache_fallback_prefix() -> None:
    code = "cache_fallback_after_bulk_failed:bulk_failed:TimeoutError"
    assert derive_manifest_reason_code([code]) == CACHE_FALLBACK_AFTER_BULK_FAILED


def test_validate_cache_policy_reason_accepts_known_reasons() -> None:
    assert validate_cache_policy_reason(CACHE_POLICY_OFFLINE_ONLY) == CACHE_POLICY_OFFLINE_ONLY
    assert validate_cache_policy_reason(CACHE_POLICY_MANIFEST_PROBE) == CACHE_POLICY_MANIFEST_PROBE


def test_format_cache_fallback_reason_normalizes_empty_input() -> None:
    assert format_cache_fallback_reason("") == "cache_fallback_after_bulk_failed:bulk_failed:unknown"


def test_derive_manifest_reason_code_handles_fetch_failed() -> None:
    assert derive_manifest_reason_code([FETCH_FAILED]) == FETCH_FAILED


def test_derive_manifest_reason_code_handles_decodo_used() -> None:
    assert derive_manifest_reason_code([DECODO_USED]) == DECODO_USED


def test_failure_reason_formatters_are_canonical() -> None:
    bulk_reason = format_bulk_failed_reason(TimeoutError("x"))
    assert bulk_reason == "bulk_failed:TimeoutError"
    surgical_reason = format_surgical_failed_reason(ValueError("y"), bulk_reason)
    assert surgical_reason == "surgical_failed:ValueError:bulk_failed:TimeoutError"


def test_classify_reason_code_maps_to_canonical_bucket() -> None:
    assert classify_reason_code("policy_cache_only_cache_hit") == POLICY_CACHE_ONLY
    assert classify_reason_code("bulk_failed:TimeoutError") == BULK_FAILED
    assert classify_reason_code("surgical_failed:ValueError:bulk_failed:TimeoutError") == SURGICAL_FAILED
    assert classify_reason_code("cache_fallback_after_bulk_failed:bulk_failed:TimeoutError") == CACHE_FALLBACK_AFTER_BULK_FAILED
    assert classify_reason_code(FETCH_FAILED) == FETCH_FAILED
    assert classify_reason_code(DECODO_USED) == DECODO_USED


def test_summarize_reason_codes_counts_canonical_buckets() -> None:
    summary = summarize_reason_codes(
        [
            "policy_cache_only_cache_hit",
            "policy_cache_only_cache_miss",
            "bulk_failed:TimeoutError",
            "cache_fallback_after_bulk_failed:bulk_failed:TimeoutError",
            "bulk_failed:ConnectionError",
        ]
    )
    assert summary == {
        BULK_FAILED: 2,
        CACHE_FALLBACK_AFTER_BULK_FAILED: 1,
        POLICY_CACHE_ONLY: 2,
    }


def test_summarize_policy_reasons_counts_nonempty_values() -> None:
    summary = summarize_policy_reasons(
        [
            CACHE_POLICY_MANIFEST_PROBE,
            "",
            "  ",
            CACHE_POLICY_OFFLINE_ONLY,
            CACHE_POLICY_MANIFEST_PROBE,
        ]
    )
    assert summary == {
        CACHE_POLICY_MANIFEST_PROBE: 2,
        CACHE_POLICY_OFFLINE_ONLY: 1,
    }


def test_summarize_policy_reasons_buckets_unknown_values() -> None:
    summary = summarize_policy_reasons(
        [
            CACHE_POLICY_MANIFEST_PROBE,
            "ad_hoc_policy",
            "another_policy",
        ]
    )
    assert summary == {
        CACHE_POLICY_MANIFEST_PROBE: 1,
        UNKNOWN_POLICY_REASON: 2,
    }


def test_canonicalize_policy_reason_normalizes_unknown_and_empty() -> None:
    assert canonicalize_policy_reason("") == ""
    assert canonicalize_policy_reason("  ") == ""
    assert canonicalize_policy_reason(CACHE_POLICY_OFFLINE_ONLY) == CACHE_POLICY_OFFLINE_ONLY
    assert canonicalize_policy_reason("custom_policy") == UNKNOWN_POLICY_REASON
