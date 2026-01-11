"""Rune adapter for OSH execution.

Expose OSH job compilation and execution via capability contracts.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.osh.executor import compile_jobs_from_dap, run_osh_jobs


def run_osh_deterministic(
    dap_json_path: str,
    run_id: str,
    out_dir: str,
    allowlist_spec_path: Optional[str] = None,
    allowlist_map_fallback_path: Optional[str] = None,
    vector_map_path: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Rune-compatible OSH executor.

    Compiles OSH jobs from DAP and executes them, returning artifacts + packets.
    """
    try:
        jobs = compile_jobs_from_dap(
            dap_json_path=dap_json_path,
            run_id=run_id,
            allowlist_spec_path=allowlist_spec_path,
            allowlist_map_fallback_path=allowlist_map_fallback_path,
            vector_map_path=vector_map_path,
        )
        artifacts, packets = run_osh_jobs(jobs, out_dir=out_dir)
        artifact_dicts = [artifact.to_dict() for artifact in artifacts]
        result = {
            "jobs_count": len(jobs),
            "artifacts": artifact_dicts,
            "packets": packets,
        }
    except Exception as exc:
        return {
            "jobs_count": 0,
            "artifacts": [],
            "packets": [],
            "not_computable": {
                "reason": str(exc),
                "missing_inputs": [],
            },
            "provenance": None,
        }

    envelope = canonical_envelope(
        result=result,
        config={},
        inputs={
            "dap_json_path": dap_json_path,
            "run_id": run_id,
            "out_dir": out_dir,
            "allowlist_spec_path": allowlist_spec_path,
            "allowlist_map_fallback_path": allowlist_map_fallback_path,
            "vector_map_path": vector_map_path,
        },
        operation_id="osh.execute",
        seed=seed,
    )

    return {
        **result,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


__all__ = ["run_osh_deterministic"]
