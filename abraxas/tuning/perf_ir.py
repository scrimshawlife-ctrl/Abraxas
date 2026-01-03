"""Performance Tuning IR - Deterministic tuning configuration.

Performance Tuning Plane v0.1 - Serializable, hash-stable IR for performance knobs.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from abraxas.tuning.schema import (
    TargetScope,
    TuningKnobs,
    TuningBudgets,
    TuningConstraints,
    TuningProvenance,
)


IR_VERSION = "0.1"


class PerfTuningIR(BaseModel):
    """Performance Tuning IR - Deterministic tuning configuration.

    This IR represents a complete, deterministic performance tuning configuration.
    All fields are explicitly set (no implicit defaults).
    """

    ir_version: str = Field(IR_VERSION, description="IR version")
    target_scope: TargetScope = Field(default_factory=TargetScope)
    knobs: TuningKnobs = Field(default_factory=TuningKnobs)
    budgets: TuningBudgets = Field(default_factory=TuningBudgets)
    constraints: TuningConstraints = Field(default_factory=TuningConstraints)
    provenance: TuningProvenance = Field(..., description="Provenance metadata")

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
    def load(cls, path: Path) -> PerfTuningIR:
        """Load IR from file.

        Args:
            path: Path to IR file

        Returns:
            Loaded PerfTuningIR

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


def get_active_ir_path() -> Path:
    """Get path to ACTIVE tuning IR pointer file.

    Returns:
        Path to ACTIVE.json pointer file
    """
    repo_root = Path(os.getenv("ABRAXAS_ROOT", Path.cwd()))
    return repo_root / ".aal" / "tuning" / "perf" / "ACTIVE.json"


def get_tuning_manifest_dir() -> Path:
    """Get directory for tuning manifests.

    Returns:
        Path to tuning manifest directory
    """
    repo_root = Path(os.getenv("ABRAXAS_ROOT", Path.cwd()))
    return repo_root / ".aal" / "tuning" / "perf"


def load_active_tuning_ir() -> PerfTuningIR | None:
    """Load the currently active tuning IR.

    Returns:
        Active PerfTuningIR or None if not set
    """
    active_path = get_active_ir_path()
    if not active_path.exists():
        return None

    # Read pointer file
    with open(active_path, "r") as f:
        pointer = json.load(f)

    manifest_path = Path(pointer["manifest_path"])
    if not manifest_path.is_absolute():
        # Resolve relative to .aal/tuning/perf
        manifest_path = get_tuning_manifest_dir() / manifest_path

    return PerfTuningIR.load(manifest_path)


def create_default_ir() -> PerfTuningIR:
    """Create default PerfTuningIR.

    Returns:
        Default PerfTuningIR with baseline settings
    """
    return PerfTuningIR(
        provenance=TuningProvenance(
            author="human",
            created_at_utc=datetime.now(timezone.utc).isoformat(),
            derived_from_runs=[],
            ledger_hashes=[],
        )
    )
