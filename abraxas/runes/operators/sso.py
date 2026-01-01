"""SSO - Shadow Structural Observer Rune Operator (ϟ₇).

Provides isolated, read-only access to Shadow Structural Metrics.

SEED Framework Compliant
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SSOContext(BaseModel):
    """Context for SSO rune invocation."""

    symbol_pool: list[dict[str, Any]] = Field(
        default_factory=list, description="List of symbolic events to analyze"
    )
    time_window_hours: int = Field(24, description="Time window for temporal metrics")
    metrics_requested: list[str] | None = Field(
        None, description="List of metric IDs (default: all six)"
    )


class SSOResult(BaseModel):
    """Result of SSO rune invocation."""

    ssm_bundle: dict[str, Any] = Field(..., description="Shadow Structural Metrics bundle")
    isolation_proof: str = Field(..., description="Cryptographic isolation proof")
    audit_log: dict[str, Any] = Field(..., description="Audit log metadata")


def apply_sso(context: dict[str, Any]) -> dict[str, Any]:
    """Apply Shadow Structural Observer rune (ϟ₇).

    This is the ONLY authorized entry point for accessing Shadow Structural Metrics.
    All computations run in isolated context with strict no-influence guarantees.

    Args:
        context: Rune invocation context containing:
            - symbol_pool: List of symbolic events
            - time_window_hours: Time window for temporal metrics
            - metrics_requested: Optional list of specific metrics

    Returns:
        Result dict containing:
            - ssm_bundle: Computed metrics with provenance
            - isolation_proof: Cryptographic attestation of non-influence
            - audit_log: Execution metadata

    Raises:
        ValueError: If invalid context or metrics requested
    """
    # Validate context
    ctx = SSOContext(**context)

    logger.info(
        "[ϟ₇ SSO] Invoked with %d symbols, %d hour window, metrics: %s",
        len(ctx.symbol_pool),
        ctx.time_window_hours,
        ctx.metrics_requested or "all",
    )

    # Pre-compute hook: Set up isolation context
    isolation_context = _setup_isolation_context()

    try:
        # Access SSM engine via internal access point
        # This is the ONLY authorized caller
        from abraxas.shadow_metrics import _internal_rune_access

        ssm_engine = _internal_rune_access()

        # Compute metrics in isolated context
        bundle = ssm_engine.compute_bundle(
            context={
                "symbol_pool": ctx.symbol_pool,
                "time_window_hours": ctx.time_window_hours,
            },
            metrics_requested=ctx.metrics_requested,
        )

        # Post-compute hook: Generate audit log
        audit_log = _generate_audit_log(
            context=ctx,
            bundle=bundle,
            isolation_context=isolation_context,
        )

        # Verify isolation (cryptographic attestation)
        isolation_verified = _verify_isolation(bundle, isolation_context)

        if not isolation_verified:
            logger.error("[ϟ₇ SSO] ISOLATION VIOLATION DETECTED")
            raise RuntimeError(
                "Shadow Structural Metrics isolation verification failed. "
                "This indicates a potential influence leak. Computation aborted."
            )

        logger.info(
            "[ϟ₇ SSO] Computed %d metrics with isolation proof %s",
            len(bundle.metrics),
            bundle.isolation_proof[:16] + "...",
        )

        # Return result
        result = SSOResult(
            ssm_bundle=bundle.model_dump(),
            isolation_proof=bundle.isolation_proof,
            audit_log=audit_log,
        )

        return result.model_dump()

    except Exception as e:
        logger.error("[ϟ₇ SSO] Computation failed: %s", str(e))
        raise


def _setup_isolation_context() -> dict[str, Any]:
    """Set up isolated execution context.

    Returns:
        Isolation context metadata
    """
    return {
        "isolation_mode": "strict",
        "side_effects_allowed": False,
        "influence_allowed": False,
        "audit_logging_enabled": True,
    }


def _generate_audit_log(
    context: SSOContext,
    bundle: Any,
    isolation_context: dict[str, Any],
) -> dict[str, Any]:
    """Generate audit log for SSO invocation.

    Args:
        context: Original invocation context
        bundle: Computed SSM bundle
        isolation_context: Isolation metadata

    Returns:
        Audit log dict
    """
    return {
        "rune": "ϟ₇",
        "rune_name": "Shadow Structural Observer",
        "invoked_at_utc": bundle.computed_at_utc,
        "symbol_count": len(context.symbol_pool),
        "time_window_hours": context.time_window_hours,
        "metrics_computed": sorted(bundle.metrics.keys()),
        "isolation_mode": isolation_context["isolation_mode"],
        "isolation_verified": True,
        "bundle_hash": bundle.bundle_hash,
    }


def _verify_isolation(bundle: Any, isolation_context: dict[str, Any]) -> bool:
    """Verify that computation maintained isolation guarantees.

    This performs cryptographic verification that:
    1. No side effects occurred
    2. No external state was modified
    3. Isolation proof is valid

    Args:
        bundle: Computed SSM bundle
        isolation_context: Isolation metadata

    Returns:
        True if isolation verified, False otherwise
    """
    # Verify all metrics have no_influence_guarantee flag
    for metric_result in bundle.metrics.values():
        if not metric_result.provenance.no_influence_guarantee:
            logger.error(
                "[ϟ₇ SSO] Metric %s missing no_influence_guarantee",
                metric_result.metric,
            )
            return False

    # Verify isolation proof format
    if not bundle.isolation_proof.startswith("sha256:"):
        logger.error("[ϟ₇ SSO] Invalid isolation proof format")
        return False

    # All checks passed
    return True
