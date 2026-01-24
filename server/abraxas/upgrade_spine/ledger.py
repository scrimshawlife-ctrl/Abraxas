from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from abraxas.core.provenance import hash_canonical_json


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _git_sha(base_path: Path) -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=base_path,
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode().strip()
    except Exception:
        return None


def environment_fingerprint(base_path: Path) -> Dict[str, Any]:
    return {
        "created_at": _utc_now_iso(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "git_sha": _git_sha(base_path),
    }


class UpgradeSpineLedger:
    def __init__(self, base_path: Path, ledger_path: Optional[Path] = None) -> None:
        self.base_path = base_path
        self.ledger_path = ledger_path or base_path / "out" / "upgrade_spine" / "ledger.jsonl"
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.touch()

    def append(self, entry_type: str, payload: Dict[str, Any]) -> str:
        entry = {
            "entry_type": entry_type,
            "payload": payload,
            "environment": environment_fingerprint(self.base_path),
        }
        entry_hash = hash_canonical_json(entry)
        entry["entry_hash"] = entry_hash
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry_hash

    def read_entries(self) -> Iterable[Dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)

    def latest_entry(self, entry_type: str, candidate_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        entries = [
            entry for entry in self.read_entries()
            if entry.get("entry_type") == entry_type
        ]
        if candidate_id is not None:
            entries = [
                entry for entry in entries
                if entry.get("payload", {}).get("candidate_id") == candidate_id
            ]
        if not entries:
            return None
        return entries[-1]

    def latest_bundle(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        return self.latest_entry("provenance_bundle", candidate_id)
