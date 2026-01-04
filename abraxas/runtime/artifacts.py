from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


def _stable_json_bytes(obj: Dict[str, Any]) -> bytes:
    """
    Deterministic JSON serialization for provenance hashing.
    """
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@dataclass(frozen=True)
class ArtifactRecord:
    schema: str
    path: str
    sha256: str
    bytes: int
    run_id: str
    tick: int
    kind: str


class ArtifactWriter:
    """
    Abraxas-owned artifact writer.
    - Writes deterministic JSON.
    - Computes sha256.
    - Appends to a per-run manifest ledger.
    """

    def __init__(self, artifacts_dir: str):
        self.root = Path(artifacts_dir)

    def write_json(
        self,
        *,
        run_id: str,
        tick: int,
        kind: str,
        schema: str,
        obj: Dict[str, Any],
        rel_path: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ArtifactRecord:
        out_path = self.root / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)

        b = _stable_json_bytes(obj)
        out_path.write_bytes(b)

        rec = ArtifactRecord(
            schema=schema,
            path=str(out_path),
            sha256=_sha256_hex(b),
            bytes=len(b),
            run_id=run_id,
            tick=int(tick),
            kind=kind,
        )

        self._append_manifest(rec, extra=extra)
        return rec

    def _append_manifest(self, rec: ArtifactRecord, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Append-only manifest update (deterministic ordering on write).
        """
        manifest_path = self.root / "manifests" / f"{rec.run_id}.manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        if manifest_path.exists():
            cur = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            cur = {
                "schema": "Manifest.v0",
                "run_id": rec.run_id,
                "records": [],
            }

        entry: Dict[str, Any] = {
            "tick": rec.tick,
            "kind": rec.kind,
            "schema": rec.schema,
            "path": rec.path,
            "sha256": rec.sha256,
            "bytes": rec.bytes,
        }
        if extra:
            # ensure stable keys in extra
            entry["extra"] = {k: extra[k] for k in sorted(extra.keys())}

        cur["records"].append(entry)

        # Deterministic sort: (tick, kind, schema, path)
        cur["records"] = sorted(
            cur["records"],
            key=lambda e: (int(e.get("tick", 0)), str(e.get("kind", "")), str(e.get("schema", "")), str(e.get("path", ""))),
        )

        manifest_path.write_bytes(_stable_json_bytes(cur))
