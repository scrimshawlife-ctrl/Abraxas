"""Patch registry for Shadow Structural Metrics.

This module maintains a write-once ledger of all incremental patches
applied to Shadow Structural Metrics implementations.

LOCKED: Baseline v1.0.0
Modification Policy: Incremental Patch Only
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class SSMPatch(BaseModel):
    """Single incremental patch to Shadow Structural Metrics."""

    patch_id: str = Field(..., description="Unique patch identifier")
    version: str = Field(..., description="Target version (MAJOR.MINOR.PATCH)")
    base_version: str = Field(..., description="Base version being patched")
    metrics_affected: list[str] = Field(..., description="List of affected metric IDs")
    description: str = Field(..., description="Human-readable patch description")
    applied_at_utc: str = Field(..., description="UTC timestamp when patch applied")
    git_sha: str | None = Field(None, description="Git commit SHA for this patch")
    backward_compatible: bool = Field(..., description="Backward compatibility flag")
    provenance_hash: str = Field(..., description="SHA256 hash of patch content")


class SSMPatchLedger(BaseModel):
    """Write-once ledger of all Shadow Structural Metrics patches."""

    baseline_version: str = Field("1.0.0", description="Baseline locked version")
    baseline_date: str = Field("2025-12-29", description="Baseline lock date")
    patches: list[SSMPatch] = Field(default_factory=list, description="Applied patches")

    def add_patch(self, patch: SSMPatch) -> None:
        """Add patch to ledger (append-only).

        Args:
            patch: Patch to add

        Raises:
            ValueError: If patch violates constraints
        """
        # Validate backward compatibility
        if not patch.backward_compatible:
            raise ValueError(
                f"Patch {patch.patch_id} violates backward compatibility requirement. "
                "All Shadow Structural Metrics patches MUST be backward compatible."
            )

        # Validate version progression
        if patch.base_version == patch.version:
            raise ValueError(
                f"Patch {patch.patch_id} has same base and target version: {patch.version}"
            )

        # Append to ledger (write-once)
        self.patches.append(patch)

    def get_current_version(self) -> str:
        """Get current SSM version after all patches.

        Returns:
            Current version string
        """
        if not self.patches:
            return self.baseline_version

        # Return version of most recent patch
        return self.patches[-1].version


# Global patch ledger (canonical)
PATCH_LEDGER = SSMPatchLedger(
    baseline_version="1.0.0",
    baseline_date="2025-12-29",
    patches=[
        SSMPatch(
            patch_id="SSM-BASELINE-1.0.0",
            version="1.0.0",
            base_version="0.0.0",
            metrics_affected=["SEI", "CLIP", "NOR", "PTS", "SCG", "FVC"],
            description="Initial canonical implementation of six Cambridge Analytica-derived metrics with SEED provenance, ABX-Runes-only coupling, and no-influence guarantees",
            applied_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z",
            git_sha="baseline",
            backward_compatible=True,
            provenance_hash="sha256:baseline-locked-2025-12-29",
        )
    ],
)


def get_ledger() -> SSMPatchLedger:
    """Get canonical patch ledger.

    Returns:
        Current patch ledger
    """
    return PATCH_LEDGER


def apply_patch(patch: SSMPatch) -> dict[str, Any]:
    """Record an incremental patch proposal to Shadow Structural Metrics.

    Canon: proposal-only. Patch application requires explicit governance
    and a separate actuator path; this registry records provenance only.

    Args:
        patch: Patch specification

    Returns:
        Patch receipt dict marking proposal-only status.

    Raises:
        ValueError: If patch violates constraints
    """
    # Add to ledger (validates constraints)
    PATCH_LEDGER.add_patch(patch)

    return {
        "status": "proposal_only",
        "patch_id": patch.patch_id,
        "version": patch.version,
        "base_version": patch.base_version,
        "metrics_affected": list(patch.metrics_affected),
    }


def validate_patch_chain() -> bool:
    """Validate integrity of patch chain.

    Returns:
        True if patch chain is valid, False otherwise
    """
    patches = PATCH_LEDGER.patches

    if not patches:
        return True

    # Verify first patch is baseline
    if patches[0].patch_id != "SSM-BASELINE-1.0.0":
        return False

    # Verify version progression
    for i in range(1, len(patches)):
        prev_patch = patches[i - 1]
        curr_patch = patches[i]

        # Current patch base should match previous patch version
        if curr_patch.base_version != prev_patch.version:
            return False

        # All patches must be backward compatible
        if not curr_patch.backward_compatible:
            return False

    return True
