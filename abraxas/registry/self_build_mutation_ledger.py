from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _get_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "UNKNOWN"


def snapshot_before_content(content: str) -> dict[str, str]:
    snapshot_id = _sha256_text(content)
    snapshot_path = Path(f"out/registry/snapshots/{snapshot_id}.json")
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot_path.exists():
        snapshot_path.write_text(content, encoding="utf-8")
    return {
        "storage": "POINTER",
        "snapshot_id": snapshot_id,
        "payload_or_ref": str(snapshot_path),
    }


def build_mutation_entry(
    approval_id: str,
    target_path: str,
    before_hash: str,
    after_hash: str,
    before_snapshot: dict[str, str],
    post_validation: dict[str, Any],
) -> dict[str, Any]:
    mutation_id = "mutation-" + _sha256_text(f"{approval_id}:{target_path}:{after_hash}")[:16]
    return {
        "schema_version": "SelfBuildMutationLedger.v1",
        "mutation_id": mutation_id,
        "approval_id": approval_id,
        "target_path": target_path,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "before_snapshot": before_snapshot,
        "rollback_ready": True,
        "post_validation": post_validation,
        "commit": _get_commit(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def append_mutation_entry(entry: dict[str, Any]) -> dict[str, Any]:
    out_path = Path("out/registry/self_build_mutation_ledger.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ledger: list[dict[str, Any]] = []
    if out_path.exists():
        try:
            loaded = json.loads(out_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("entries"), list):
                ledger = loaded["entries"]
        except Exception:
            ledger = []

    ledger.append(entry)
    payload = {
        "schema_version": "SelfBuildMutationLedgerCollection.v1",
        "entry_count": len(ledger),
        "entries": ledger,
    }
    payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
