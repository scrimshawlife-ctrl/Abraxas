from __future__ import annotations

from typing import Any, Dict, List, Tuple
import json
import os

from .types import sha256_hex, stable_json_dumps


def compute_report(
    envelope: Any, *, dsp_runs: List[Tuple[Any, ...]], fusion_runs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Minimal determinism report.
    """
    # Report uses stable hashes to support quick sanity checks.
    dsp_hashes = [sha256_hex(stable_json_dumps(list(run))) for run in dsp_runs]
    fusion_hashes = [sha256_hex(stable_json_dumps(g)) for g in fusion_runs]
    return {
        "run_count": len(dsp_runs),
        "dsp_hashes": dsp_hashes,
        "fusion_hashes": fusion_hashes,
        "all_dsp_equal": len(set(dsp_hashes)) <= 1,
        "all_fusion_equal": len(set(fusion_hashes)) <= 1,
    }


def write_report(report: Dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)

