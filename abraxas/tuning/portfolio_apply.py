"""Atomic apply layer for portfolio tuning IR.

Universal Tuning Plane v0.4 - Portfolio-wide atomic apply/rollback.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from abraxas.tuning.portfolio_ir import (
    PortfolioTuningIR,
    get_portfolio_active_path,
    get_portfolio_manifest_dir,
)


ApplyStatus = Literal["ok", "validation_error", "apply_error"]


class PortfolioApplyResult:
    """Result of applying portfolio tuning IR."""

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


def validate_portfolio_ir(ir: PortfolioTuningIR) -> list[str]:
    """Validate portfolio tuning IR for correctness.

    Args:
        ir: PortfolioTuningIR to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check IR version
    if ir.ir_version != "0.4":
        errors.append(f"Unsupported IR version: {ir.ir_version}")

    # Check perf knobs
    if ir.module_knobs.perf.zstd_level_hot < 1 or ir.module_knobs.perf.zstd_level_hot > 6:
        errors.append(
            f"perf.zstd_level_hot out of range: {ir.module_knobs.perf.zstd_level_hot}"
        )

    if (
        ir.module_knobs.perf.zstd_level_cold < 3
        or ir.module_knobs.perf.zstd_level_cold > 22
    ):
        errors.append(
            f"perf.zstd_level_cold out of range: {ir.module_knobs.perf.zstd_level_cold}"
        )

    # Check acquisition knobs
    if ir.module_knobs.acquisition.max_requests_per_run < 1:
        errors.append(
            f"acquisition.max_requests_per_run must be >= 1: {ir.module_knobs.acquisition.max_requests_per_run}"
        )

    if ir.module_knobs.acquisition.decodo_max_per_run < 0:
        errors.append(
            f"acquisition.decodo_max_per_run must be >= 0: {ir.module_knobs.acquisition.decodo_max_per_run}"
        )

    # Check pipeline knobs
    if ir.module_knobs.pipeline.retention_days_live_mode < 1:
        errors.append(
            f"pipeline.retention_days_live_mode must be >= 1: {ir.module_knobs.pipeline.retention_days_live_mode}"
        )

    if ir.module_knobs.pipeline.max_in_memory_bytes < 1_000_000:
        errors.append(
            f"pipeline.max_in_memory_bytes must be >= 1MB: {ir.module_knobs.pipeline.max_in_memory_bytes}"
        )

    # Check UBV violations
    violations = []
    for dim_name, dim_value in ir.ubv.items():
        if isinstance(dim_value, dict) and "hard_limit" in dim_value:
            measured = dim_value.get("measured", 0)
            hard_limit = dim_value.get("hard_limit")
            if hard_limit is not None and measured > hard_limit:
                violations.append(
                    f"{dim_name}: {measured} exceeds hard limit {hard_limit}"
                )

    if violations:
        errors.append(f"UBV hard limit violations: {', '.join(violations)}")

    return errors


def apply_portfolio_ir_atomically(
    ir: PortfolioTuningIR,
    run_ctx: dict,
    *,
    mode: Literal["active", "canary"] = "canary",
) -> PortfolioApplyResult:
    """Apply portfolio tuning IR atomically.

    Args:
        ir: PortfolioTuningIR to apply
        run_ctx: Run context with run_id
        mode: "active" or "canary" (canary = shadow deployment)

    Returns:
        PortfolioApplyResult with status and paths
    """
    # Validate IR
    errors = validate_portfolio_ir(ir)
    if errors:
        return PortfolioApplyResult(status="validation_error", errors=errors)

    try:
        # Generate manifest path
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_id = run_ctx.get("run_id", "UNKNOWN")
        manifest_filename = f"portfolio_tuning_{timestamp}_{run_id}.json"

        manifest_dir = get_portfolio_manifest_dir()
        manifest_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = manifest_dir / manifest_filename

        # Save IR to manifest
        ir_hash = ir.save(manifest_path)

        # Update ACTIVE pointer atomically (only if mode = "active")
        if mode == "active":
            active_path = get_portfolio_active_path()
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
            canary_path = get_portfolio_active_path().with_name("CANARY.json")
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

        return PortfolioApplyResult(
            status="ok",
            manifest_path=manifest_path,
            active_hash=ir_hash,
        )

    except Exception as e:
        return PortfolioApplyResult(
            status="apply_error",
            errors=[f"Failed to apply portfolio IR: {str(e)}"],
        )


def rollback_portfolio_to_previous(run_ctx: dict) -> PortfolioApplyResult:
    """Rollback to previous portfolio ACTIVE tuning IR.

    Args:
        run_ctx: Run context with run_id

    Returns:
        PortfolioApplyResult with status
    """
    active_path = get_portfolio_active_path()
    if not active_path.exists():
        return PortfolioApplyResult(
            status="apply_error", errors=["No ACTIVE portfolio tuning to rollback from"]
        )

    try:
        # Read current ACTIVE
        with open(active_path, "r") as f:
            current_pointer = json.load(f)

        # Backup current ACTIVE
        backup_path = active_path.with_name("ACTIVE.backup.json")
        shutil.copy(active_path, backup_path)

        # Remove ACTIVE to revert to default
        # (In production, would maintain manifest history and point to previous)
        active_path.unlink()

        return PortfolioApplyResult(
            status="ok",
            errors=[],
        )

    except Exception as e:
        return PortfolioApplyResult(
            status="apply_error",
            errors=[f"Failed to rollback portfolio: {str(e)}"],
        )
