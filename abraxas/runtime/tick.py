"""
Abraxas Runtime — Canonical Tick Orchestrator

This module owns:
- ERS scheduler execution
- Artifact emission (TrendPack, provenance bundles)
- Structured tick output

This is the single canonical stitch-point between scheduler, artifacts, and runtime context.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Callable, Optional

from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable
from abraxas.viz import ers_trace_to_trendpack
from abraxas.runtime.artifacts import ArtifactWriter
from abraxas.runtime.pipeline_bindings import PipelineBindings, resolve_pipeline_bindings
from abraxas.runtime.results_pack import build_results_pack, make_result_ref
from abraxas.runtime.view_pack import build_view_pack
from abraxas.runtime.policy_snapshot import ensure_policy_snapshot, policy_ref_from_snapshot
from abraxas.runtime.run_header import ensure_run_header
from abraxas.runtime.stability_read import read_stability_summary
from abraxas.detectors.shadow.normalize import wrap_shadow_task


def abraxas_tick(
    *,
    tick: int,
    run_id: str,
    mode: str,
    context: Dict[str, Any],
    artifacts_dir: str,
    # Native bindings: resolved from repo when None
    bindings: Optional[PipelineBindings] = None,
    # Legacy parameters: kept for backward compatibility with tests
    # If provided, these override the bindings (test mode)
    run_signal: Optional[Callable[[Dict[str, Any]], Any]] = None,
    run_compress: Optional[Callable[[Dict[str, Any]], Any]] = None,
    run_overlay: Optional[Callable[[Dict[str, Any]], Any]] = None,
    run_shadow_tasks: Optional[Dict[str, Callable[[Dict[str, Any]], Any]]] = None,
) -> Dict[str, Any]:
    """
    Canonical Abraxas tick orchestrator.
    - Runs ERS scheduler with deterministic ordering
    - Emits TrendPack artifact (Abraxas-owned)
    - Emits RunIndex artifact (Abraxas-owned)
    - Writes manifest records with SHA-256
    - Returns structured tick output with artifact references

    This is where runtime meets scheduler - the only layer that legitimately knows:
    - What executed (ERS trace)
    - What the run identity is (run_id/tick/mode)
    - Where artifacts live (artifacts_dir)

    Args:
        tick: Current tick number
        run_id: Run identifier for provenance
        mode: Execution mode (e.g., "live", "test", "backtest")
        context: Shared context dict passed to all pipeline functions
        artifacts_dir: Directory for artifact emission
        bindings: Optional PipelineBindings (resolved from repo if None)
        run_signal: Legacy param - override signal function (for tests)
        run_compress: Legacy param - override compress function (for tests)
        run_overlay: Legacy param - override overlay function (for tests)
        run_shadow_tasks: Legacy param - override shadow tasks (for tests)

    Returns:
        Dict with tick results, remaining budgets, and artifact references
    """

    # Resolve pipeline functions
    # Priority: explicit legacy params > bindings > auto-resolve
    if run_signal is not None and run_compress is not None and run_overlay is not None:
        # Legacy mode: all three explicit params provided (backward compat)
        actual_signal = run_signal
        actual_compress = run_compress
        actual_overlay = run_overlay
        actual_shadow = run_shadow_tasks or {}
        bindings_provenance = {
            "bindings": "legacy_explicit",
            "oracle": {
                "signal": "explicit",
                "compress": "explicit",
                "overlay": "explicit",
            },
            "shadow": {
                "provider": "explicit" if run_shadow_tasks else None,
                "task_count": len(run_shadow_tasks) if run_shadow_tasks else 0,
            },
        }
    elif bindings is not None:
        # Bindings explicitly provided
        actual_signal = bindings.run_signal
        actual_compress = bindings.run_compress
        actual_overlay = bindings.run_overlay
        actual_shadow = bindings.shadow_tasks
        bindings_provenance = bindings.provenance
    else:
        # Auto-resolve from repo (native mode)
        resolved = resolve_pipeline_bindings()
        actual_signal = resolved.run_signal
        actual_compress = resolved.run_compress
        actual_overlay = resolved.run_overlay
        actual_shadow = resolved.shadow_tasks
        bindings_provenance = resolved.provenance

    s = DeterministicScheduler()

    # Forecast lane (primary)
    s.add(bind_callable(name="oracle:signal",   lane="forecast", priority=0, cost_ops=10, fn=actual_signal))
    s.add(bind_callable(name="oracle:compress", lane="forecast", priority=1, cost_ops=10, fn=actual_compress))
    s.add(bind_callable(name="oracle:overlay",  lane="forecast", priority=2, cost_ops=10, fn=actual_overlay))

    # Shadow lane (observation-only)
    # Stable ordering by name via scheduler keying
    # Wrap each shadow task to normalize outputs to canonical shape
    for name, fn in sorted(actual_shadow.items(), key=lambda kv: kv[0]):
        wrapped = wrap_shadow_task(name, fn)
        s.add(bind_callable(name=f"shadow:{name}", lane="shadow", priority=0, cost_ops=2, fn=wrapped))

    out = s.run_tick(
        tick=tick,
        budget_forecast=Budget(ops=50, entropy=0),
        budget_shadow=Budget(ops=20, entropy=0),
        context=context,
    )

    # === STRICTLY HERE: Abraxas artifact emission ===
    aw = ArtifactWriter(artifacts_dir)

    # Capture PolicyRef.v0 via immutable snapshot for provenance continuity
    # Snapshot path: policy_snapshots/<run_id>/retention.<sha>.policysnapshot.json
    retention_policy_path = str(Path(artifacts_dir) / "policy" / "retention.json")
    snap_path, snap_sha = ensure_policy_snapshot(
        artifacts_dir=artifacts_dir,
        run_id=run_id,
        policy_name="retention",
        policy_path=retention_policy_path,
    )
    pol_ref = policy_ref_from_snapshot("retention", snap_path, snap_sha)

    # RunHeader written once per run_id (contains heavy provenance)
    run_header_path, run_header_sha256 = ensure_run_header(
        artifacts_dir=artifacts_dir,
        run_id=run_id,
        mode=mode,
        pipeline_bindings_provenance=bindings_provenance,
        policy_refs={"retention": pol_ref},
        repo_root=None,  # optionally set to repo root if available in context
    )

    # 1) Write ResultsPack first (so TrendPack can point at it)
    results_pack = build_results_pack(
        run_id=run_id,
        tick=out["tick"],
        results=out["results"],
        provenance={"engine": "abraxas", "mode": mode, "ers": "v0.2", "policy_ref": pol_ref},
    )

    results_pack_rec = aw.write_json(
        run_id=run_id,
        tick=tick,
        kind="results_pack",
        schema="ResultsPack.v0",
        obj=results_pack,
        rel_path=f"results/{run_id}/{tick:06d}.resultspack.json",
        extra={"mode": mode, "policy_ref": pol_ref},
    )

    # 2) Build deterministic result_ref map for TrendPack events
    result_ref_by_task = {}
    for e in out["trace"]:
        result_ref_by_task[e.task] = make_result_ref(
            results_pack_path=results_pack_rec.path,
            task_name=e.task,
        )

    # 3) Build TrendPack with result refs injected
    trendpack = ers_trace_to_trendpack(
        trace=out["trace"],
        run_id=run_id,
        tick=out["tick"],
        provenance={
            "engine": "abraxas",
            "mode": mode,
            "ers": "v0.2",
            "pipeline_bindings": bindings_provenance,
            "policy_ref": pol_ref,
        },
        result_ref_by_task=result_ref_by_task,
    )

    trendpack_rec = aw.write_json(
        run_id=run_id,
        tick=tick,
        kind="trendpack",
        schema="TrendPack.v0",
        obj=trendpack,
        rel_path=f"viz/{run_id}/{tick:06d}.trendpack.json",
        extra={"mode": mode, "ers": "v0.2", "policy_ref": pol_ref},
    )

    # 4) Minimal RunIndex.v0 (Abraxas-side) — references TrendPack, ResultsPack, and RunHeader
    runindex = {
        "schema": "RunIndex.v0",
        "run_id": run_id,
        "tick": int(tick),
        "refs": {
            "trendpack": trendpack_rec.path,
            "results_pack": results_pack_rec.path,
            "run_header": run_header_path,
        },
        "hashes": {
            "trendpack_sha256": trendpack_rec.sha256,
            "results_pack_sha256": results_pack_rec.sha256,
        },
        "tags": [],
        "provenance": {
            "engine": "abraxas",
            "mode": mode,
            "policy_ref": pol_ref,
            "run_header_sha256": run_header_sha256,
        },
    }

    runindex_rec = aw.write_json(
        run_id=run_id,
        tick=tick,
        kind="runindex",
        schema="RunIndex.v0",
        obj=runindex,
        rel_path=f"run_index/{run_id}/{tick:06d}.runindex.json",
        extra={"mode": mode, "policy_ref": pol_ref},
    )

    # 5) ViewPack: one-file overview artifact for UIs
    # Keep it compact & high-signal by only resolving errors/skips
    # Include invariance summary so UIs can show stable/unstable badge without extra loads
    # Include stability summary if run-level stability record exists (for PASS/FAIL badge)
    stability_summary = read_stability_summary(artifacts_dir, run_id)
    view_pack = build_view_pack(
        trendpack_path=trendpack_rec.path,
        run_id=run_id,
        tick=tick,
        mode=mode,
        resolve_limit=50,
        resolve_only_status=["error", "skipped_budget"],
        invariance={
            "schema": "InvarianceSummary.v0",
            "trendpack_sha256": trendpack_rec.sha256,
            "runheader_sha256": run_header_sha256,
            "passed": bool(trendpack_rec.sha256) and bool(run_header_sha256),
        },
        stability_summary=stability_summary,
        provenance={"engine": "abraxas", "mode": mode, "policy_ref": pol_ref},
    )

    viewpack_rec = aw.write_json(
        run_id=run_id,
        tick=tick,
        kind="viewpack",
        schema="ViewPack.v0",
        obj=view_pack,
        rel_path=f"view/{run_id}/{tick:06d}.viewpack.json",
        extra={"mode": mode, "policy_ref": pol_ref},
    )

    return {
        "tick": out["tick"],
        "run_id": run_id,
        "mode": mode,
        "results": {k: asdict(v) for k, v in out["results"].items()},
        "remaining": {
            "forecast": asdict(out["remaining"]["forecast"]),
            "shadow": asdict(out["remaining"]["shadow"]),
        },
        "artifacts": {
            "trendpack": trendpack_rec.path,
            "trendpack_sha256": trendpack_rec.sha256,
            "results_pack": results_pack_rec.path,
            "results_pack_sha256": results_pack_rec.sha256,
            "runindex": runindex_rec.path,
            "runindex_sha256": runindex_rec.sha256,
            "viewpack": viewpack_rec.path,
            "viewpack_sha256": viewpack_rec.sha256,
            "run_header": run_header_path,
            "run_header_sha256": run_header_sha256,
        },
    }


__all__ = ["abraxas_tick"]
