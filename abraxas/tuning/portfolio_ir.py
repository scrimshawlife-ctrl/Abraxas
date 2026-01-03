"""Portfolio Tuning IR - Multi-subsystem tuning configuration.

Universal Tuning Plane v0.4 - Cross-module tuning IR with unified budgets.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from abraxas.tuning.schema import (
    TuningKnobs as PerfKnobs,
    TuningProvenance,
)
from abraxas.tuning.ubv import UniversalBudgetVector


IR_VERSION = "0.4"

Granularity = Literal["hourly", "daily", "weekly", "monthly"]
DeltaSamplingPolicy = Literal["all", "major_only", "adaptive"]


class AcquisitionKnobs(BaseModel):
    """Acquisition subsystem tuning knobs."""

    batch_window_preferred: list[str] = Field(
        ["daily", "weekly"], description="Preferred batch windows (ordered)"
    )
    max_requests_per_run: int = Field(
        100, description="Maximum requests per acquisition run", ge=1
    )
    cache_only_fallback: bool = Field(
        True, description="Fall back to cache-only mode on quota exhaustion"
    )
    decodo_policy_enabled: bool = Field(
        False, description="Enable Decodo surgical acquisition"
    )
    decodo_max_per_run: int = Field(5, description="Max Decodo requests per run", ge=0)


class PipelineKnobs(BaseModel):
    """Pipeline subsystem tuning knobs."""

    window_granularity: list[Granularity] = Field(
        ["weekly", "daily"], description="Analysis window granularity (ordered)"
    )
    retention_days_live_mode: int = Field(
        30, description="Days to retain in live mode", ge=1
    )
    lazy_load_packets: bool = Field(True, description="Lazy load packets on demand")
    max_in_memory_bytes: int = Field(
        100_000_000, description="Maximum bytes in memory at once", ge=1_000_000
    )


class AtlasKnobs(BaseModel):
    """Atlas (export/render) subsystem tuning knobs.

    Note: Atlas operations are pure (no side effects), knobs affect batching only.
    """

    export_granularity: Granularity = Field(
        "weekly", description="Granularity for exports"
    )
    delta_sampling_policy: DeltaSamplingPolicy | None = Field(
        None, description="Delta sampling policy (None = full exports)"
    )


class ModuleKnobs(BaseModel):
    """Unified module knobs wrapper."""

    perf: PerfKnobs = Field(default_factory=PerfKnobs)
    acquisition: AcquisitionKnobs = Field(default_factory=AcquisitionKnobs)
    pipeline: PipelineKnobs = Field(default_factory=PipelineKnobs)
    atlas: AtlasKnobs = Field(default_factory=AtlasKnobs)


class PortfolioProvenance(BaseModel):
    """Provenance for portfolio tuning."""

    derived_from_runs: list[str] = Field(
        default_factory=list, description="Run IDs used for optimization"
    )
    ledger_hashes: list[str] = Field(
        default_factory=list, description="Ledger hashes used for metrics"
    )
    author: Literal["portfolio_optimizer", "human"] = Field(
        "portfolio_optimizer", description="Who created this portfolio"
    )
    created_at_utc: str = Field(..., description="ISO8601 timestamp")
    baseline_ubv_hash: str | None = Field(
        None, description="Hash of baseline UBV used for optimization"
    )


class PortfolioTuningIR(BaseModel):
    """Portfolio Tuning IR - Multi-subsystem tuning configuration.

    This IR wraps all subsystem knobs and enforces unified budget constraints.
    """

    ir_version: str = Field(IR_VERSION, description="IR version")
    ubv: dict = Field(..., description="Universal Budget Vector (serialized)")
    module_knobs: ModuleKnobs = Field(default_factory=ModuleKnobs)
    provenance: PortfolioProvenance = Field(..., description="Provenance metadata")

    def canonical_json(self) -> str:
        """Generate canonical JSON representation (sorted keys, stable)."""
        return json.dumps(
            self.model_dump(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def ir_hash(self) -> str:
        """Compute SHA-256 hash of canonical JSON."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def save(self, path: Path) -> str:
        """Save IR to file and return hash.

        Args:
            path: Path to save IR to

        Returns:
            SHA-256 hash of IR
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write canonical JSON
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.canonical_json() + "\n")

        # Write hash sidecar
        ir_hash = self.ir_hash()
        with open(path.with_suffix(".hash"), "w", encoding="utf-8") as f:
            f.write(ir_hash + "\n")

        return ir_hash

    @classmethod
    def load(cls, path: Path) -> PortfolioTuningIR:
        """Load IR from file.

        Args:
            path: Path to IR file

        Returns:
            Loaded PortfolioTuningIR

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If hash doesn't match
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ir = cls(**data)

        # Verify hash if sidecar exists
        hash_path = path.with_suffix(".hash")
        if hash_path.exists():
            with open(hash_path, "r") as f:
                expected_hash = f.read().strip()

            actual_hash = ir.ir_hash()
            if actual_hash != expected_hash:
                raise ValueError(
                    f"Hash mismatch: expected {expected_hash}, got {actual_hash}"
                )

        return ir


def get_portfolio_active_path() -> Path:
    """Get path to portfolio ACTIVE pointer file.

    Returns:
        Path to portfolio ACTIVE.json
    """
    repo_root = Path(os.getenv("ABRAXAS_ROOT", Path.cwd()))
    return repo_root / ".aal" / "tuning" / "portfolio" / "ACTIVE.json"


def get_portfolio_manifest_dir() -> Path:
    """Get directory for portfolio manifests.

    Returns:
        Path to portfolio manifest directory
    """
    repo_root = Path(os.getenv("ABRAXAS_ROOT", Path.cwd()))
    return repo_root / ".aal" / "tuning" / "portfolio"


def load_active_portfolio_ir() -> PortfolioTuningIR | None:
    """Load the currently active portfolio IR.

    Returns:
        Active PortfolioTuningIR or None if not set
    """
    active_path = get_portfolio_active_path()
    if not active_path.exists():
        return None

    # Read pointer file
    with open(active_path, "r") as f:
        pointer = json.load(f)

    manifest_path = Path(pointer["manifest_path"])
    if not manifest_path.is_absolute():
        # Resolve relative to .aal/tuning/portfolio
        manifest_path = get_portfolio_manifest_dir() / manifest_path

    return PortfolioTuningIR.load(manifest_path)


def create_default_portfolio_ir(ubv: UniversalBudgetVector) -> PortfolioTuningIR:
    """Create default PortfolioTuningIR with baseline settings.

    Args:
        ubv: Universal Budget Vector to use

    Returns:
        Default PortfolioTuningIR
    """
    import hashlib

    ubv_dict = ubv.to_dict()
    ubv_json = json.dumps(ubv_dict, sort_keys=True)
    ubv_hash = hashlib.sha256(ubv_json.encode()).hexdigest()

    return PortfolioTuningIR(
        ubv=ubv_dict,
        provenance=PortfolioProvenance(
            author="human",
            created_at_utc=datetime.now(timezone.utc).isoformat(),
            derived_from_runs=[],
            ledger_hashes=[],
            baseline_ubv_hash=ubv_hash,
        ),
    )
