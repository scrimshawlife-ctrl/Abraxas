from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, Mapping, Optional


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def attach_evidence_pointers(
    *,
    envelope: Dict[str, Any],
    paths: Mapping[str, str] | None = None,
    hashes: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """
    Attach evidence pointers (paths/hashes) to the envelope.
    Add-only: creates oracle_signal.evidence if needed.
    """
    if paths is None and hashes is None:
        return envelope

    sig = envelope.setdefault("oracle_signal", {})
    ev = sig.setdefault("evidence", {})
    if not isinstance(ev, dict):
        sig["evidence"] = {}
        ev = sig["evidence"]

    if paths:
        ev.setdefault("paths", {})
        for k, p in paths.items():
            if isinstance(k, str) and k.strip() and isinstance(p, str) and p.strip():
                ev["paths"][k] = p

    if hashes:
        ev.setdefault("hashes", {})
        for k, hv in hashes.items():
            if isinstance(k, str) and k.strip() and isinstance(hv, str) and hv.strip():
                ev["hashes"][k] = hv

    # Clean empties
    if isinstance(ev.get("paths"), dict) and not ev["paths"]:
        ev.pop("paths", None)
    if isinstance(ev.get("hashes"), dict) and not ev["hashes"]:
        ev.pop("hashes", None)
    if not ev:
        sig.pop("evidence", None)

    return envelope


def attach_evidence_from_files(
    *,
    envelope: Dict[str, Any],
    files: Mapping[str, str],
    compute_hashes: bool = True,
) -> Dict[str, Any]:
    """
    Convenience: given a mapping name->filepath, attach only existing files.
    Optionally compute sha256 hashes for existing files.
    """
    paths_out: Dict[str, str] = {}
    hashes_out: Dict[str, str] = {}
    for k, p in files.items():
        if not (isinstance(k, str) and k.strip() and isinstance(p, str) and p.strip()):
            continue
        if os.path.exists(p) and os.path.isfile(p):
            paths_out[k] = p
            if compute_hashes:
                hashes_out[k] = _sha256_file(p)
    return attach_evidence_pointers(envelope=envelope, paths=paths_out, hashes=(hashes_out if compute_hashes else None))
