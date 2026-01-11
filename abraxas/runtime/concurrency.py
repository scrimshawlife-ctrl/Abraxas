"""Concurrency configuration for deterministic parallel stages."""

from __future__ import annotations

from dataclasses import dataclass

from abraxas.policy.utp import PipelineKnobs, PortfolioTuningIR


@dataclass(frozen=True)
class ConcurrencyConfig:
    enabled: bool = False
    max_workers_fetch: int = 4
    max_workers_parse: int = 4
    max_inflight_bytes: int = 50_000_000
    deterministic_commit: bool = True
    ordering_key: tuple[str, ...] = ("source_id", "window_start_utc", "cache_key", "url")

    def workers_for_stage(self, stage: str) -> int:
        if not self.enabled:
            return 1
        if stage == "FETCH":
            return max(1, int(self.max_workers_fetch))
        if stage == "PARSE":
            return max(1, int(self.max_workers_parse))
        return 1

    @classmethod
    def from_portfolio(cls, portfolio: PortfolioTuningIR) -> "ConcurrencyConfig":
        knobs = portfolio.pipeline
        cap = max(1, int(portfolio.ubv.max_requests_per_run))
        return cls(
            enabled=knobs.concurrency_enabled,
            max_workers_fetch=min(knobs.max_workers_fetch, cap),
            max_workers_parse=min(knobs.max_workers_parse, cap),
            max_inflight_bytes=knobs.max_inflight_bytes,
        )
