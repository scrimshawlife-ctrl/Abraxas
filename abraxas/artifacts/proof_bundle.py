from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from abx.util.hashutil import sha256_file


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if isinstance(data, dict):
        return data
    return None


def generate_proof_bundle(
    *,
    run_id: str,
    artifacts: Dict[str, str],
    bundle_root: str = "out/proof_bundles",
    ledger_pointer: Optional[Dict[str, Any]] = None,
    ts: Optional[str] = None,
) -> Dict[str, Any]:
    ts = ts or _utc_now_iso()
    bundle_dir = Path(bundle_root) / run_id
    bundle_dir.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    artifact_records: Dict[str, Dict[str, Any]] = {}

    for label, src_path in artifacts.items():
        src = Path(src_path)
        if not src.exists():
            missing.append(label)
            artifact_records[label] = {"path": src_path, "present": False}
            continue
        dest = bundle_dir / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        artifact_records[label] = {
            "path": dest.name,
            "present": True,
            "sha256": sha256_file(dest),
            "bytes": dest.stat().st_size,
        }

    ledger_pointer_path = bundle_dir / "ledger_pointer.json"
    if ledger_pointer is None:
        ledger_pointer = {}
    ledger_pointer_payload = {
        "version": "ledger_pointer.v0.1",
        "run_id": run_id,
        "ts": ts,
        "ledgers": ledger_pointer,
    }
    _write_json(ledger_pointer_path, ledger_pointer_payload)

    ledger_entry = {
        "path": ledger_pointer_path.name,
        "present": True,
        "sha256": sha256_file(ledger_pointer_path),
        "bytes": ledger_pointer_path.stat().st_size,
    }

    policy_flags: Dict[str, Any] = {"non_truncation": {}, "missing_artifacts": missing}
    for label, record in artifact_records.items():
        if not record.get("present"):
            continue
        path = bundle_dir / record["path"]
        if path.suffix != ".json":
            continue
        data = _read_json(path)
        policy = (data or {}).get("policy") or {}
        policy_flags["non_truncation"][label] = bool(policy.get("non_truncation"))

    counts = {
        "files_present": len([r for r in artifact_records.values() if r.get("present")]) + 1,
        "json_present": len(
            [
                r
                for r in artifact_records.values()
                if r.get("present") and Path(r["path"]).suffix == ".json"
            ]
        )
        + 1,
        "md_present": len(
            [
                r
                for r in artifact_records.values()
                if r.get("present") and Path(r["path"]).suffix == ".md"
            ]
        ),
    }

    manifest_payload = {
        "version": "proof_bundle_manifest.v0.1",
        "run_id": run_id,
        "ts": ts,
        "bundle_dir": str(bundle_dir),
        "artifacts": artifact_records,
        "ledger_pointer": ledger_entry,
        "counts": counts,
        "policy_flags": policy_flags,
    }
    manifest_path = bundle_dir / "bundle_manifest.json"
    _write_json(manifest_path, manifest_payload)

    return {
        "bundle_dir": str(bundle_dir),
        "bundle_manifest": str(manifest_path),
        "ledger_pointer": str(ledger_pointer_path),
        "missing": missing,
    }
