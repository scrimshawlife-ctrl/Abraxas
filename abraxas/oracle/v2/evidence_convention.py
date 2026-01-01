from __future__ import annotations

import os
from typing import Any, Dict, Mapping

from abraxas.oracle.v2.export import compute_run_id
from abraxas.oracle.v2.evidence import attach_evidence_from_files


def evidence_dir_for_envelope(envelope: Dict[str, Any], out_dir: str = "out") -> str:
    """
    Deterministic evidence directory aligned to export run_id:
      out/<run_id>/evidence/
    """
    run_id = compute_run_id(envelope)
    return os.path.join(out_dir, run_id, "evidence")


def evidence_paths(
    *,
    envelope: Dict[str, Any],
    out_dir: str = "out",
    names: list[str] | None = None,
    ext: str = ".json",
) -> Dict[str, str]:
    """
    Pre-compute deterministic file paths for evidence artifacts.
    Caller may write to these paths.
    """
    ed = evidence_dir_for_envelope(envelope, out_dir=out_dir)
    os.makedirs(ed, exist_ok=True)
    nms = names or []
    out: Dict[str, str] = {}
    for nm in nms:
        if isinstance(nm, str) and nm.strip():
            out[nm] = os.path.join(ed, f"{nm}{ext}")
    return out


def attach_evidence_from_run_dir(
    *,
    envelope: Dict[str, Any],
    out_dir: str = "out",
    files: Mapping[str, str],
    compute_hashes: bool = True,
) -> Dict[str, Any]:
    """
    Given a mapping name->filename (not full path), resolves into
    out/<run_id>/evidence/<filename> and attaches pointers for existing files.
    """
    ed = evidence_dir_for_envelope(envelope, out_dir=out_dir)
    resolved: Dict[str, str] = {}
    for k, fname in files.items():
        if isinstance(k, str) and k.strip() and isinstance(fname, str) and fname.strip():
            resolved[k] = os.path.join(ed, fname)
    return attach_evidence_from_files(envelope=envelope, files=resolved, compute_hashes=compute_hashes)
