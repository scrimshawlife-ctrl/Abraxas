"""Canonical acquisition reason codes and derivation helpers."""

from __future__ import annotations

from typing import Iterable, Literal, Optional, cast

CACHE_POLICY_OFFLINE_ONLY = "offline_cache_only_policy"
CACHE_POLICY_MANIFEST_PROBE = "manifest_cache_probe"
OFFLINE_CACHE_MISS = "offline_cache_miss"
POLICY_CACHE_ONLY_CACHE_HIT = "policy_cache_only_cache_hit"
POLICY_CACHE_ONLY_CACHE_MISS = "policy_cache_only_cache_miss"
POLICY_CACHE_ONLY = "policy_cache_only"
SURGICAL_FAILED = "surgical_failed"
BULK_FAILED = "bulk_failed"
CACHE_FALLBACK_AFTER_BULK_FAILED = "cache_fallback_after_bulk_failed"
CACHE_HIT = "cache_hit"
FETCH_FAILED = "fetch_failed"
DECODO_USED = "decodo"
CachePolicyReason = Literal["offline_cache_only_policy", "manifest_cache_probe"]
UNKNOWN_POLICY_REASON = "unknown_policy_reason"

ALLOWED_CACHE_POLICY_REASONS = {
    CACHE_POLICY_OFFLINE_ONLY,
    CACHE_POLICY_MANIFEST_PROBE,
}

__all__ = [
    "CACHE_POLICY_OFFLINE_ONLY",
    "CACHE_POLICY_MANIFEST_PROBE",
    "OFFLINE_CACHE_MISS",
    "POLICY_CACHE_ONLY_CACHE_HIT",
    "POLICY_CACHE_ONLY_CACHE_MISS",
    "POLICY_CACHE_ONLY",
    "SURGICAL_FAILED",
    "BULK_FAILED",
    "CACHE_FALLBACK_AFTER_BULK_FAILED",
    "CACHE_HIT",
    "FETCH_FAILED",
    "DECODO_USED",
    "CachePolicyReason",
    "UNKNOWN_POLICY_REASON",
    "ALLOWED_CACHE_POLICY_REASONS",
    "validate_cache_policy_reason",
    "derive_manifest_reason_code",
    "format_cache_fallback_reason",
    "format_bulk_failed_reason",
    "format_surgical_failed_reason",
    "classify_reason_code",
    "summarize_reason_codes",
    "canonicalize_policy_reason",
    "summarize_policy_reasons",
]


def validate_cache_policy_reason(reason: str) -> CachePolicyReason:
    normalized = str(reason).strip()
    if not normalized:
        raise RuntimeError("cache-only fetch requires explicit policy_reason")
    if normalized not in ALLOWED_CACHE_POLICY_REASONS:
        allowed = ", ".join(sorted(ALLOWED_CACHE_POLICY_REASONS))
        raise RuntimeError(
            f"invalid cache-only policy_reason: {normalized!r}. "
            f"Allowed values: {allowed}"
        )
    return cast(CachePolicyReason, normalized)


def classify_reason_code(code: str) -> str:
    normalized = str(code or "").strip()
    if not normalized:
        return ""
    if normalized.startswith("policy_cache_only_"):
        return POLICY_CACHE_ONLY
    if normalized.startswith("surgical_failed:"):
        return SURGICAL_FAILED
    if normalized.startswith("bulk_failed:"):
        return BULK_FAILED
    if CACHE_FALLBACK_AFTER_BULK_FAILED in normalized:
        return CACHE_FALLBACK_AFTER_BULK_FAILED
    if normalized == CACHE_HIT:
        return CACHE_HIT
    if normalized == FETCH_FAILED:
        return FETCH_FAILED
    if normalized == DECODO_USED:
        return DECODO_USED
    return normalized


def derive_manifest_reason_code(reason_codes: Iterable[str]) -> Optional[str]:
    codes = [str(code) for code in reason_codes if code]
    if not codes:
        return None
    classified = [classify_reason_code(code) for code in codes]
    if all(code == POLICY_CACHE_ONLY for code in classified):
        return POLICY_CACHE_ONLY
    if any(code == SURGICAL_FAILED for code in classified):
        return SURGICAL_FAILED
    if any(code == BULK_FAILED for code in classified):
        return BULK_FAILED
    if any(code == CACHE_FALLBACK_AFTER_BULK_FAILED for code in classified):
        return CACHE_FALLBACK_AFTER_BULK_FAILED
    if any(code == CACHE_HIT for code in classified):
        return CACHE_HIT
    if any(code == FETCH_FAILED for code in classified):
        return FETCH_FAILED
    if any(code == DECODO_USED for code in classified):
        return DECODO_USED
    return codes[0]


def format_cache_fallback_reason(bulk_reason: str) -> str:
    normalized = str(bulk_reason).strip() or "bulk_failed:unknown"
    return f"{CACHE_FALLBACK_AFTER_BULK_FAILED}:{normalized}"


def format_bulk_failed_reason(exc: Exception) -> str:
    return f"{BULK_FAILED}:{type(exc).__name__}"


def format_surgical_failed_reason(exc: Exception, bulk_reason: str) -> str:
    return f"{SURGICAL_FAILED}:{type(exc).__name__}:{bulk_reason}"


def summarize_reason_codes(reason_codes: Iterable[str]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for raw in reason_codes:
        code = classify_reason_code(raw)
        if not code:
            continue
        summary[code] = summary.get(code, 0) + 1
    return dict(sorted(summary.items()))


def canonicalize_policy_reason(policy_reason: str) -> str:
    normalized = str(policy_reason or "").strip()
    if not normalized:
        return ""
    if normalized not in ALLOWED_CACHE_POLICY_REASONS:
        return UNKNOWN_POLICY_REASON
    return normalized


def summarize_policy_reasons(policy_reasons: Iterable[str]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for raw in policy_reasons:
        key = canonicalize_policy_reason(str(raw or "").strip())
        if not key:
            continue
        summary[key] = summary.get(key, 0) + 1
    return dict(sorted(summary.items()))
