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
import json
from typing import Any, Dict, Callable, Optional

from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable
from abraxas.viz import ers_trace_to_trendpack


def _write_json(path: Path, obj: Dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    path.write_text(data, encoding="utf-8")
    return str(path)


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

    artifact_path = Path(artifacts_dir) / "viz" / run_id / f"{tick:06d}.trendpack.json"
    trendpack_ref = _write_json(artifact_path, trendpack)

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
            "trendpack": trendpack_ref,
        },
    }


__all__ = ["abraxas_tick"]
