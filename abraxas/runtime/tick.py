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
from typing import Any, Dict, Callable, Optional

from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable
from abraxas.viz import ers_trace_to_trendpack
from abraxas.runtime.artifacts import ArtifactWriter


def abraxas_tick(
    *,
    tick: int,
    run_id: str,
    mode: str,
    context: Dict[str, Any],
    artifacts_dir: str,
    # These are your *existing* pipeline steps; pass the real functions from your engine.
    run_signal: Callable[[Dict[str, Any]], Any],
    run_compress: Callable[[Dict[str, Any]], Any],
    run_overlay: Callable[[Dict[str, Any]], Any],
    # Optional shadow steps
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
    """

    s = DeterministicScheduler()

    # Forecast lane (primary)
    s.add(bind_callable(name="oracle:signal",   lane="forecast", priority=0, cost_ops=10, fn=run_signal))
    s.add(bind_callable(name="oracle:compress", lane="forecast", priority=1, cost_ops=10, fn=run_compress))
    s.add(bind_callable(name="oracle:overlay",  lane="forecast", priority=2, cost_ops=10, fn=run_overlay))

    # Shadow lane (observation-only)
    if run_shadow_tasks:
        # stable ordering by name via scheduler keying
        for name, fn in sorted(run_shadow_tasks.items(), key=lambda kv: kv[0]):
            s.add(bind_callable(name=f"shadow:{name}", lane="shadow", priority=0, cost_ops=2, fn=fn))

    out = s.run_tick(
        tick=tick,
        budget_forecast=Budget(ops=50, entropy=0),
        budget_shadow=Budget(ops=20, entropy=0),
        context=context,
    )

    # === STRICTLY HERE: Abraxas artifact emission ===
    aw = ArtifactWriter(artifacts_dir)

    trendpack = ers_trace_to_trendpack(
        trace=out["trace"],
        run_id=run_id,
        tick=out["tick"],
        provenance={
            "engine": "abraxas",
            "mode": mode,
            "ers": "v0.2",
        },
    )

    trendpack_rec = aw.write_json(
        run_id=run_id,
        tick=tick,
        kind="trendpack",
        schema="TrendPack.v0",
        obj=trendpack,
        rel_path=f"viz/{run_id}/{tick:06d}.trendpack.json",
        extra={"mode": mode, "ers": "v0.2"},
    )

    # Minimal RunIndex.v0 (Abraxas-side)
    runindex = {
        "schema": "RunIndex.v0",
        "run_id": run_id,
        "tick": int(tick),
        "refs": {"trendpack": trendpack_rec.path},
        "hashes": {"trendpack_sha256": trendpack_rec.sha256},
        "tags": [],
        "provenance": {"engine": "abraxas", "mode": mode},
    }

    runindex_rec = aw.write_json(
        run_id=run_id,
        tick=tick,
        kind="runindex",
        schema="RunIndex.v0",
        obj=runindex,
        rel_path=f"run_index/{run_id}/{tick:06d}.runindex.json",
        extra={"mode": mode},
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
            "runindex": runindex_rec.path,
            "runindex_sha256": runindex_rec.sha256,
        },
    }


__all__ = ["abraxas_tick"]
