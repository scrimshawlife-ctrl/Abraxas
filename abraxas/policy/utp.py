"""Unified Tuning Protocol (UTP) budgets and decodo policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json, sha256_hex


@dataclass(frozen=True)
class DecodoPolicy:
    max_requests: int = 1
    manifest_only: bool = True


@dataclass(frozen=True)
class UBVBudgets:
    max_requests_per_run: int = 50
    max_bytes_per_run: int = 10_000_000
    batch_window: str = "daily"
    decodo_policy: DecodoPolicy = field(default_factory=DecodoPolicy)


@dataclass(frozen=True)
class PipelineKnobs:
    concurrency_enabled: bool = False
    max_workers_fetch: int = 4
    max_workers_parse: int = 4
    max_inflight_bytes: int = 50_000_000


@dataclass(frozen=True)
class PortfolioTuningIR:
    portfolio_id: str = "acquisition_default"
    ubv: UBVBudgets = field(default_factory=UBVBudgets)
    pipeline: PipelineKnobs = field(default_factory=PipelineKnobs)

    def hash(self) -> str:
        payload = {
            "portfolio_id": self.portfolio_id,
            "ubv": {
                "max_requests_per_run": self.ubv.max_requests_per_run,
                "max_bytes_per_run": self.ubv.max_bytes_per_run,
                "batch_window": self.ubv.batch_window,
                "decodo_policy": {
                    "max_requests": self.ubv.decodo_policy.max_requests,
                    "manifest_only": self.ubv.decodo_policy.manifest_only,
                },
            },
            "pipeline": {
                "concurrency_enabled": self.pipeline.concurrency_enabled,
                "max_workers_fetch": self.pipeline.max_workers_fetch,
                "max_workers_parse": self.pipeline.max_workers_parse,
                "max_inflight_bytes": self.pipeline.max_inflight_bytes,
            },
        }
        return sha256_hex(canonical_json(payload))


def load_active_utp(base_dir: str | Path = "data/utp") -> PortfolioTuningIR:
    base_dir = Path(base_dir)
    active_pointer = base_dir / "ACTIVE"
    if active_pointer.exists():
        target = active_pointer.read_text(encoding="utf-8").strip()
        if target:
            active_path = base_dir / target
            if active_path.exists():
                return load_portfolio(active_path)
    return PortfolioTuningIR()


def load_portfolio(path: str | Path) -> PortfolioTuningIR:
    payload = _load_json(Path(path))
    return _utp_from_payload(payload)


def find_portfolio_by_hash(base_dir: str | Path, portfolio_hash: str) -> Path | None:
    base_dir = Path(base_dir)
    for path in sorted(base_dir.glob("*.json")):
        try:
            portfolio = load_portfolio(path)
        except Exception:
            continue
        if portfolio.hash() == portfolio_hash:
            return path
    return None


def _utp_from_payload(payload: Dict[str, Any]) -> PortfolioTuningIR:
    ubv = payload.get("ubv") or {}
    decodo = ubv.get("decodo_policy") or {}
    pipeline = payload.get("pipeline") or {}
    return PortfolioTuningIR(
        portfolio_id=payload.get("portfolio_id", "acquisition_default"),
        ubv=UBVBudgets(
            max_requests_per_run=int(ubv.get("max_requests_per_run", 50)),
            max_bytes_per_run=int(ubv.get("max_bytes_per_run", 10_000_000)),
            batch_window=str(ubv.get("batch_window", "daily")),
            decodo_policy=DecodoPolicy(
                max_requests=int(decodo.get("max_requests", 1)),
                manifest_only=bool(decodo.get("manifest_only", True)),
            ),
        ),
        pipeline=PipelineKnobs(
            concurrency_enabled=bool(pipeline.get("concurrency_enabled", False)),
            max_workers_fetch=int(pipeline.get("max_workers_fetch", 4)),
            max_workers_parse=int(pipeline.get("max_workers_parse", 4)),
            max_inflight_bytes=int(pipeline.get("max_inflight_bytes", 50_000_000)),
        ),
    )


def _load_json(path: Path) -> Dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))
