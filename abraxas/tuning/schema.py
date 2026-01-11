"""Pydantic schemas for Performance Tuning IR.

Performance Tuning Plane v0.1 - Deterministic tuning configuration schemas.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Codec = Literal["zstd", "gzip", "lz4", "none"]
BatchWindow = Literal["hourly", "daily", "weekly", "monthly"]
ReasonCode = Literal["BLOCKED", "MANIFEST_DISCOVERY", "JS_REQUIRED", "FALLBACK"]


class CodecPolicy(BaseModel):
    """Codec selection policy."""

    default: Codec = Field("zstd", description="Default codec for normal operations")
    hot: Codec = Field("lz4", description="Codec for hot/fast path")
    cold: Codec = Field("zstd", description="Codec for cold/archive path")


class DictRetrainPolicy(BaseModel):
    """Dictionary retraining policy."""

    min_days_between: int = Field(30, description="Minimum days between retraining", ge=1)
    drift_threshold: float = Field(
        0.2, description="Drift threshold for triggering retrain", ge=0.0, le=1.0
    )
    sample_cap: int = Field(100, description="Maximum samples for training", ge=10)


class BatchWindowPolicy(BaseModel):
    """Batch window sizing policy."""

    preferred: list[BatchWindow] = Field(
        ["daily"], description="Preferred batch windows (ordered)"
    )
    max_requests_per_run: int = Field(1000, description="Maximum requests per run", ge=1)


class DecododoPolicy(BaseModel):
    """Decodo surgical acquisition policy."""

    enabled: bool = Field(False, description="Enable Decodo surgical acquisition")
    max_requests_per_run: int = Field(5, description="Maximum Decodo requests per run", ge=1)
    allowed_reason_codes: list[ReasonCode] = Field(
        ["MANIFEST_DISCOVERY"], description="Allowed reason codes for Decodo"
    )
    require_manifest_only: bool = Field(
        True, description="Only allow manifest discovery (no arbitrary scraping)"
    )


class TuningKnobs(BaseModel):
    """Performance tuning knobs."""

    codec: CodecPolicy = Field(default_factory=CodecPolicy)
    zstd_level_hot: int = Field(1, description="Zstd level for hot path", ge=1, le=6)
    zstd_level_cold: int = Field(3, description="Zstd level for cold path", ge=3, le=22)
    dict_enabled: bool = Field(True, description="Enable dictionary compression")
    dict_retrain_policy: DictRetrainPolicy = Field(default_factory=DictRetrainPolicy)
    hot_cache_days: int = Field(7, description="Days to keep in hot cache", ge=1)
    cold_archive_after_days: int = Field(90, description="Archive after N days", ge=1)
    batch_window: BatchWindowPolicy = Field(default_factory=BatchWindowPolicy)
    decodo_policy: DecododoPolicy = Field(default_factory=DecododoPolicy)


class TuningBudgets(BaseModel):
    """ERS budget constraints."""

    max_ms_per_run: int | None = Field(None, description="Maximum ms per run")
    max_bytes_written_per_run: int | None = Field(
        None, description="Maximum bytes written per run"
    )
    max_network_calls_per_run: int | None = Field(
        None, description="Maximum network calls per run"
    )


class TuningConstraints(BaseModel):
    """Hard constraints on tuning."""

    determinism_required: bool = Field(
        True, description="Determinism required (cannot be relaxed)"
    )
    cache_required_for_network: bool = Field(
        True, description="Cache required for all network calls"
    )
    no_domain_prior: bool = Field(True, description="No domain-specific priors allowed")


class TuningProvenance(BaseModel):
    """Provenance metadata for tuning IR."""

    derived_from_runs: list[str] = Field(
        default_factory=list, description="Run IDs this tuning was derived from"
    )
    ledger_hashes: list[str] = Field(
        default_factory=list, description="Perf ledger hashes used for tuning"
    )
    author: Literal["autotune", "human"] = Field(
        "autotune", description="Who created this tuning"
    )
    created_at_utc: str = Field(..., description="ISO8601 timestamp of creation")


class TargetScope(BaseModel):
    """Scope of tuning application."""

    source_ids: list[str] = Field(
        ["*"], description="Source IDs to apply tuning to (* for all)"
    )
    artifact_kinds: list[str] = Field(
        ["raw", "parsed", "packets", "ledger"],
        description="Artifact kinds to apply tuning to",
    )
