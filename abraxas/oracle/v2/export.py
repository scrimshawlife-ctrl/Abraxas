from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Tuple


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def compute_run_id(envelope: Dict[str, Any]) -> str:
    """
    Deterministic run id:
      sha256(window.start_iso + config_hash + mode + decision_fingerprint)[:16]
    Falls back to safe placeholders when keys missing.
    """
    sig = envelope.get("oracle_signal", {}) or {}
    win = sig.get("window", {}) or {}
    start_iso = str(win.get("start_iso", "NO_WINDOW"))
    v2 = sig.get("v2", {}) or {}
    mode = str(v2.get("mode", "NO_MODE"))
    md = v2.get("mode_decision", {}) or {}
    fp = str(md.get("fingerprint", "NO_FP"))
    compliance = v2.get("compliance", {}) or {}
    cfg = str((compliance.get("provenance") or {}).get("config_hash", "NO_CFG"))
    base = f"{start_iso}|{cfg}|{mode}|{fp}"
    return _sha256_hex(base)[:16]


def export_run(
    *,
    envelope: Dict[str, Any],
    surface: Dict[str, Any],
    out_dir: str = "out",
) -> Dict[str, Any]:
    """
    Writes deterministic artifacts:
      out/<run_id>/surface.json
      out/<run_id>/envelope.json
      out/<run_id>/manifest.json
    """
    run_id = compute_run_id(envelope)
    run_path = os.path.join(out_dir, run_id)
    os.makedirs(run_path, exist_ok=True)

    surface_s = _stable_json(surface)
    env_s = _stable_json(envelope)

    surface_hash = _sha256_hex(surface_s)
    envelope_hash = _sha256_hex(env_s)

    # manifest carries the governance pointers
    v2 = (envelope.get("oracle_signal", {}) or {}).get("v2", {}) or {}
    compliance = v2.get("compliance", {}) or {}
    cfg = (compliance.get("provenance") or {}).get("config_hash")
    md = v2.get("mode_decision", {}) or {}

    manifest = {
        "run_id": run_id,
        "paths": {
            "surface": os.path.join(run_path, "surface.json"),
            "envelope": os.path.join(run_path, "envelope.json"),
            "manifest": os.path.join(run_path, "manifest.json"),
        },
        "hashes": {
            "surface_sha256": surface_hash,
            "envelope_sha256": envelope_hash,
        },
        "governance": {
            "mode": v2.get("mode"),
            "mode_decision_fingerprint": md.get("fingerprint"),
            "compliance_status": compliance.get("status"),
            "config_hash": cfg,
        },
    }

    with open(os.path.join(run_path, "surface.json"), "w", encoding="utf-8") as f:
        f.write(surface_s + "\n")
    with open(os.path.join(run_path, "envelope.json"), "w", encoding="utf-8") as f:
        f.write(env_s + "\n")
    with open(os.path.join(run_path, "manifest.json"), "w", encoding="utf-8") as f:
        f.write(_stable_json(manifest) + "\n")

    return manifest
