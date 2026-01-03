"""ABX-Rune Tuning Layer - Performance tuning operations.

Performance Tuning Plane v0.1 - Runes for canary workflow.

Implements five tuning runes:
- ABX-PERF_SUMMARIZE (ß‚„): Reads ledger ’ summary stats
- ABX-PERF_TUNE_PROPOSE (ß‚…): Summary ’ candidate IR
- ABX-PERF_TUNE_CANARY (ß‚†): Apply candidate in canary mode
- ABX-PERF_TUNE_PROMOTE (ß‚‡): Promote canary to ACTIVE
- ABX-PERF_TUNE_REVOKE (ß‚ˆ): Revert to previous ACTIVE
"""

from __future__ import annotations

from typing import Any, Dict

from abraxas.tuning.objectives import compute_rent_metrics
from abraxas.tuning.optimizer import propose_tuning
from abraxas.tuning.apply import apply_ir_atomically, rollback_to_previous
from abraxas.tuning.gates import check_rent_gates
from abraxas.tuning.perf_ir import load_active_tuning_ir


def apply_perf_summarize(
    window_hours: int,
    run_ctx: Dict[str, Any],
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply ABX-PERF_SUMMARIZE rune - read ledger and compute summary stats.

    Args:
        window_hours: Time window in hours for metrics
        run_ctx: Run context with run_id
        strict_execution: If True, raises NotImplementedError for unimplemented

    Returns:
        Dict with keys: metrics, summary_hash, provenance
    """
    run_id = run_ctx.get("run_id", "SUMMARIZE_RUN")

    # Compute rent metrics from perf ledger
    metrics = compute_rent_metrics(window_hours=window_hours)

    # Convert to dict for return
    metrics_dict = {
        "avg_compression_ratio_by_source": metrics.avg_compression_ratio_by_source,
        "p95_duration_ms_by_op": metrics.p95_duration_ms_by_op,
        "cache_hit_rate_by_source": metrics.cache_hit_rate_by_source,
        "network_calls_by_source": metrics.network_calls_by_source,
        "decodo_calls_by_reason": metrics.decodo_calls_by_reason,
        "storage_growth_rate": metrics.storage_growth_rate,
        "total_bytes_saved": metrics.total_bytes_saved,
    }

    # Compute deterministic hash
    import json
    import hashlib
    summary_json = json.dumps(metrics_dict, sort_keys=True)
    summary_hash = hashlib.sha256(summary_json.encode()).hexdigest()

    return {
        "metrics": metrics_dict,
        "summary_hash": summary_hash,
        "provenance": {
            "run_id": run_id,
            "window_hours": window_hours,
        },
    }


def apply_perf_tune_propose(
    summary: Dict[str, Any],
    run_ctx: Dict[str, Any],
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply ABX-PERF_TUNE_PROPOSE rune - propose candidate IR.

    Args:
        summary: Summary from PERF_SUMMARIZE
        run_ctx: Run context
        strict_execution: If True, raises NotImplementedError

    Returns:
        Dict with keys: proposal_ir, predicted_improvement, risk_score, rationale
    """
    run_id = run_ctx.get("run_id", "PROPOSE_RUN")

    # Load current IR (baseline)
    baseline_ir = load_active_tuning_ir()

    # Propose tuning
    proposal = propose_tuning(
        baseline_ir=baseline_ir,
        window_hours=168,  # 7 days
        run_id=run_id,
    )

    return {
        "proposal_ir": proposal.ir.model_dump(),
        "predicted_improvement": proposal.predicted_improvement,
        "risk_score": proposal.risk_score,
        "rationale": proposal.rationale,
        "baseline_objective": proposal.baseline_objective,
        "proposed_objective": proposal.proposed_objective,
    }


def apply_perf_tune_canary(
    proposal_ir: Dict[str, Any],
    run_ctx: Dict[str, Any],
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply ABX-PERF_TUNE_CANARY rune - apply candidate in canary mode.

    Args:
        proposal_ir: Proposed IR from PERF_TUNE_PROPOSE
        run_ctx: Run context
        strict_execution: If True, raises NotImplementedError

    Returns:
        Dict with keys: status, canary_path, ir_hash
    """
    from abraxas.tuning.perf_ir import PerfTuningIR

    run_id = run_ctx.get("run_id", "CANARY_RUN")

    # Parse IR
    ir = PerfTuningIR(**proposal_ir)

    # Apply in canary mode
    result = apply_ir_atomically(ir, run_ctx, mode="canary")

    return {
        "status": result.status,
        "canary_path": str(result.manifest_path) if result.manifest_path else None,
        "ir_hash": result.active_hash,
        "errors": result.errors,
    }


def apply_perf_tune_promote(
    metrics_before: Dict[str, Any],
    metrics_after: Dict[str, Any],
    run_ctx: Dict[str, Any],
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply ABX-PERF_TUNE_PROMOTE rune - promote canary to ACTIVE if rent gates pass.

    Args:
        metrics_before: Metrics before canary
        metrics_after: Metrics after canary
        run_ctx: Run context
        strict_execution: If True, raises NotImplementedError

    Returns:
        Dict with keys: promoted, gate_results, rationale
    """
    from abraxas.tuning.objectives import RentMetrics
    from abraxas.tuning.perf_ir import PerfTuningIR
    import json

    run_id = run_ctx.get("run_id", "PROMOTE_RUN")

    # Reconstruct RentMetrics
    metrics_before_obj = RentMetrics(**metrics_before)
    metrics_after_obj = RentMetrics(**metrics_after)

    # Check rent gates
    verdict = check_rent_gates(metrics_before_obj, metrics_after_obj)

    if verdict.passed:
        # Load canary IR
        from abraxas.tuning.perf_ir import get_active_ir_path
        canary_path = get_active_ir_path().with_name("CANARY.json")

        if canary_path.exists():
            with open(canary_path, "r") as f:
                canary_pointer = json.load(f)

            # Load canary IR manifest
            from pathlib import Path
            from abraxas.tuning.perf_ir import get_tuning_manifest_dir
            manifest_path = Path(canary_pointer["manifest_path"])
            if not manifest_path.is_absolute():
                manifest_path = get_tuning_manifest_dir() / manifest_path

            canary_ir = PerfTuningIR.load(manifest_path)

            # Apply as ACTIVE
            result = apply_ir_atomically(canary_ir, run_ctx, mode="active")

            return {
                "promoted": True,
                "gate_results": verdict.gate_results,
                "rationale": verdict.rationale,
                "active_path": str(result.manifest_path),
                "ir_hash": result.active_hash,
            }
        else:
            return {
                "promoted": False,
                "gate_results": verdict.gate_results,
                "rationale": "No canary found",
            }
    else:
        return {
            "promoted": False,
            "gate_results": verdict.gate_results,
            "rationale": verdict.rationale,
        }


def apply_perf_tune_revoke(
    run_ctx: Dict[str, Any],
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply ABX-PERF_TUNE_REVOKE rune - revert to previous ACTIVE.

    Args:
        run_ctx: Run context
        strict_execution: If True, raises NotImplementedError

    Returns:
        Dict with keys: revoked, errors
    """
    result = rollback_to_previous(run_ctx)

    return {
        "revoked": result.status == "ok",
        "errors": result.errors,
    }
