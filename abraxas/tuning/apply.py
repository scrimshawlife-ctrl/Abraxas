"""Atomic apply layer for performance tuning IR.

Performance Tuning Plane v0.1 - Atomic apply/rollback with ERS integration.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from abraxas.tuning.perf_ir import (
    PerfTuningIR,
    get_active_ir_path,
    get_tuning_manifest_dir,
)


ApplyStatus = Literal["ok", "validation_error", "apply_error"]


class ApplyResult:
    """Result of applying tuning IR."""

    def __init__(
        self,
        status: ApplyStatus,
        manifest_path: Path | None = None,
        active_hash: str | None = None,
        errors: list[str] | None = None,
    ):
        self.status = status
        self.manifest_path = manifest_path
        self.active_hash = active_hash
        self.errors = errors or []


def validate_ir(ir: PerfTuningIR) -> list[str]:
    """Validate tuning IR for correctness.

    Args:
        ir: PerfTuningIR to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check IR version
    if ir.ir_version != "0.1":
        errors.append(f"Unsupported IR version: {ir.ir_version}")

    # Check knob constraints
    if ir.knobs.zstd_level_hot < 1 or ir.knobs.zstd_level_hot > 6:
        errors.append(f"zstd_level_hot out of range: {ir.knobs.zstd_level_hot}")

    if ir.knobs.zstd_level_cold < 3 or ir.knobs.zstd_level_cold > 22:
        errors.append(f"zstd_level_cold out of range: {ir.knobs.zstd_level_cold}")

    if ir.knobs.hot_cache_days < 1:
        errors.append(f"hot_cache_days must be >= 1: {ir.knobs.hot_cache_days}")

    if ir.knobs.cold_archive_after_days < 1:
        errors.append(
            f"cold_archive_after_days must be >= 1: {ir.knobs.cold_archive_after_days}"
        )

    # Check that hot cache < cold archive
    if ir.knobs.hot_cache_days >= ir.knobs.cold_archive_after_days:
        errors.append("hot_cache_days must be < cold_archive_after_days")

    # Check determinism constraint (cannot be relaxed)
    if not ir.constraints.determinism_required:
        errors.append("determinism_required constraint cannot be False")

    if not ir.constraints.cache_required_for_network:
        errors.append("cache_required_for_network constraint cannot be False")

    # Check budget constraints are non-negative
    if ir.budgets.max_ms_per_run is not None and ir.budgets.max_ms_per_run < 0:
        errors.append("max_ms_per_run must be non-negative")

    if (
        ir.budgets.max_bytes_written_per_run is not None
        and ir.budgets.max_bytes_written_per_run < 0
    ):
        errors.append("max_bytes_written_per_run must be non-negative")

    if (
        ir.budgets.max_network_calls_per_run is not None
        and ir.budgets.max_network_calls_per_run < 0
    ):
        errors.append("max_network_calls_per_run must be non-negative")

    return errors


def apply_ir_atomically(
    ir: PerfTuningIR,
    run_ctx: dict,
    *,
    mode: Literal["active", "canary"] = "canary",
) -> ApplyResult:
    """Apply tuning IR atomically.

    Args:
        ir: PerfTuningIR to apply
        run_ctx: Run context with run_id
        mode: "active" or "canary" (canary = shadow deployment)

    Returns:
        ApplyResult with status and paths
    """
    # Validate IR
    errors = validate_ir(ir)
    if errors:
        return ApplyResult(status="validation_error", errors=errors)

    try:
        # Generate manifest path
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_id = run_ctx.get("run_id", "UNKNOWN")
        manifest_filename = f"perf_tuning_{timestamp}_{run_id}.json"

        manifest_dir = get_tuning_manifest_dir()
        manifest_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = manifest_dir / manifest_filename

        # Save IR to manifest
        ir_hash = ir.save(manifest_path)

        # Update ACTIVE pointer atomically (only if mode = "active")
        if mode == "active":
            active_path = get_active_ir_path()
            temp_active_path = active_path.with_suffix(".tmp")

            # Write to temp file
            pointer = {
                "manifest_path": str(manifest_path.relative_to(manifest_dir.parent)),
                "ir_hash": ir_hash,
                "applied_at_utc": datetime.now(timezone.utc).isoformat(),
                "run_id": run_id,
                "mode": mode,
            }

            with open(temp_active_path, "w") as f:
                json.dump(pointer, f, indent=2, sort_keys=True)
                f.write("\n")

            # Atomic replace
            temp_active_path.replace(active_path)

        # Canary mode: save pointer to CANARY.json instead
        elif mode == "canary":
            canary_path = get_active_ir_path().with_name("CANARY.json")
            pointer = {
                "manifest_path": str(manifest_path.relative_to(manifest_dir.parent)),
                "ir_hash": ir_hash,
                "applied_at_utc": datetime.now(timezone.utc).isoformat(),
                "run_id": run_id,
                "mode": mode,
            }

            with open(canary_path, "w") as f:
                json.dump(pointer, f, indent=2, sort_keys=True)
                f.write("\n")

        return ApplyResult(
            status="ok",
            manifest_path=manifest_path,
            active_hash=ir_hash,
        )

    except Exception as e:
        return ApplyResult(
            status="apply_error",
            errors=[f"Failed to apply IR: {str(e)}"],
        )


def rollback_to_previous(run_ctx: dict) -> ApplyResult:
    """Rollback to previous ACTIVE tuning IR.

    Args:
        run_ctx: Run context with run_id

    Returns:
        ApplyResult with status
    """
    active_path = get_active_ir_path()
    if not active_path.exists():
        return ApplyResult(status="apply_error", errors=["No ACTIVE tuning to rollback from"])

    try:
        # Read current ACTIVE
        with open(active_path, "r") as f:
            current_pointer = json.load(f)

        # Find previous manifest (would need manifest history tracking)
        # For now, just remove ACTIVE to revert to default
        backup_path = active_path.with_name("ACTIVE.backup.json")
        shutil.copy(active_path, backup_path)
        active_path.unlink()

        return ApplyResult(
            status="ok",
            errors=[],
        )

    except Exception as e:
        return ApplyResult(
            status="apply_error",
            errors=[f"Failed to rollback: {str(e)}"],
        )
