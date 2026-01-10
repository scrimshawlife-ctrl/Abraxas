"""Rune adapter for OSH capabilities.

Thin adapter layer exposing abraxas.osh.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from abraxas.core.provenance import canonical_envelope
from abraxas.osh.executor import (
    compile_jobs_from_dap as compile_jobs_from_dap_core,
    run_osh_jobs as run_osh_jobs_core,
)


def compile_jobs_from_dap_deterministic(
    dap_json_path: str,
    run_id: str,
    allowlist_spec_path: Optional[str] = None,
    allowlist_map_fallback_path: Optional[str] = None,
    vector_map_path: Optional[str] = None,
    max_actions_per_run: int = 10,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible OSH job compiler.

    Compiles fetch jobs from DAP (Decodo Action Plan).

    Args:
        dap_json_path: Path to dap_<run_id>.json
        run_id: Run identifier
        allowlist_spec_path: Path to allowlist spec YAML/JSON
        allowlist_map_fallback_path: Fallback JSON mapping
        vector_map_path: Vector map YAML/JSON path
        max_actions_per_run: Maximum actions to process
        seed: Deterministic seed (for provenance)

    Returns:
        Dict with jobs, provenance, not_computable
    """
    jobs = compile_jobs_from_dap_core(
        dap_json_path=dap_json_path,
        run_id=run_id,
        allowlist_spec_path=allowlist_spec_path,
        allowlist_map_fallback_path=allowlist_map_fallback_path,
        vector_map_path=vector_map_path,
        max_actions_per_run=max_actions_per_run,
    )

    # Convert jobs to dicts for serialization
    jobs_dicts = [job.__dict__ if hasattr(job, '__dict__') else job for job in jobs]

    envelope = canonical_envelope(
        result={"jobs": jobs_dicts, "job_count": len(jobs)},
        config={"max_actions_per_run": max_actions_per_run},
        inputs={
            "dap_json_path": dap_json_path,
            "run_id": run_id,
            "allowlist_spec_path": allowlist_spec_path,
            "allowlist_map_fallback_path": allowlist_map_fallback_path,
            "vector_map_path": vector_map_path,
        },
        operation_id="osh.compile_jobs_from_dap",
        seed=seed
    )

    return {
        "jobs": jobs,  # Return original job objects for use
        "job_count": len(jobs),
        "provenance": envelope["provenance"],
        "not_computable": None
    }


def run_osh_jobs_deterministic(
    jobs: List[Any],
    out_dir: str = "out",
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible OSH job executor.

    Executes compiled OSH fetch jobs.

    Args:
        jobs: List of OSHFetchJob objects
        out_dir: Output directory for artifacts
        seed: Deterministic seed (for provenance)

    Returns:
        Dict with artifacts, packets, provenance, not_computable
    """
    artifacts, packets = run_osh_jobs_core(jobs, out_dir=out_dir)

    envelope = canonical_envelope(
        result={
            "artifact_count": len(artifacts),
            "packet_count": len(packets),
        },
        config={"out_dir": out_dir},
        inputs={"job_count": len(jobs)},
        operation_id="osh.run_jobs",
        seed=seed
    )

    return {
        "artifacts": artifacts,
        "packets": packets,
        "artifact_count": len(artifacts),
        "packet_count": len(packets),
        "provenance": envelope["provenance"],
        "not_computable": None
    }


__all__ = [
    "compile_jobs_from_dap_deterministic",
    "run_osh_jobs_deterministic",
]
